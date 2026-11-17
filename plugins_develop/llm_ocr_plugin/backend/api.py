from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import base64
import json
import httpx
import asyncio
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.user_ai_config import UserAIConfig
from app.core.security import get_current_user

router = APIRouter(prefix="/api/plugins/llm_ocr", tags=["llm_ocr"])

GLM_OCR_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"

OCR_SYSTEM_PROMPT = """你是一个专业的数学与编程题目识别助手。请提取图片中的题目并返回严格的 JSON 数组。
要求：
1. 按大题号切分。如果同一题有(1)(2)小问，必须放在同一个 description 里，用 <br/> 隔开。
2. 所有数学符号必须用 $ 包裹。
3. LaTeX 里的反斜杠 \\ 必须双写转义为 \\\\。
返回格式：
[
  {
    "title": "题号",
    "description": "题目内容"
  }
]
不要输出任何其他解释，不要使用 ```json 代码块包裹。"""

def fix_json_latex(json_str: str) -> str:
    try:
        commands = ["lim", "frac", "sum", "int", "sqrt", "alpha", "beta", "gamma", "theta", "lambda", "pi", "rho", "sigma", "tau", "phi", "chi", "psi", "omega", "to", "infty", "neq", "times", "vert", "lvert", "rvert", "mid", "cdots", "dots", "quad", "qquad", "text", "sup", "geqslant", "in"]
        for cmd in commands:
            json_str = re.sub(r'(?<!\\)\\' + cmd + r'(?![a-zA-Z])', r'\\\\' + cmd, json_str)
    except Exception as e:
        print(f"[LLM OCR] 正则修复反斜杠失败: {e}")
    return json_str

# 【核心修复】统一的 LaTeX 清洗函数
def clean_latex(text: str) -> str:
    if not text: return text
    
    # 1. 修复绝对值。KaTeX 对纯竖线 | 的支持最稳
    text = text.replace('\\lvert', '|').replace('\\rvert', '|').replace('\\vert', '|').replace('\\mid', '|')
    
    # 2. 【核心修复】统一极限语法。把可能出现的 \lim_{ 或 \lim_\limits_{ 统一转为合法的 \lim\limits_{
    # 这样绝对不会再报 Missing open brace for subscript
    text = re.sub(r'\\lim_?\s*(\\limits)?_?\s*\{', r'\\lim\\limits_{', text)
    
    # 3. 清除被 Python 吃掉的控制字符
    text = text.replace('\x0c', '\\f').replace('\x08', '\\b').replace('\x0b', '\\v')
    
    return text

@router.post("/parse")
async def parse_image_with_llm(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserAIConfig).where(UserAIConfig.user_id == current_user.id))
    user_config = result.scalar_one_or_none()
    if not user_config or not user_config.config:
        raise HTTPException(status_code=400, detail="请先在设置中配置 AI 模型")

    config = user_config.config
    active_profile = config.get("profiles", {}).get(config.get("current_profile"), {})
    api_key = (active_profile.get("api_key") or "").strip()
    base_url = (active_profile.get("base_url") or "").strip()
    model_name = (active_profile.get("model") or "").strip()

    if not api_key:
        raise HTTPException(status_code=400, detail="AI Key 未配置")
    
    contents = await file.read()
    mime_type = file.content_type or "image/jpeg"
    base64_image = base64.b64encode(contents).decode('utf-8')

    # ==========================================
    # 分支 1：专用 GLM-OCR
    # ==========================================
    if "glm-ocr" in model_name.lower():
        payload = {
            "model": "glm-ocr",
            "file": base64_image
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
            try:
                resp = await client.post(GLM_OCR_ENDPOINT, headers=headers, json=payload)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=f"GLM-OCR 报错: {resp.text}")
                    
                res_data = resp.json()
                md_text = res_data.get("md_results", "")
                if not md_text:
                    md_text = str(res_data.get("layout_details", ""))
                
                parts = re.split(r'\n(?=\d+[\.\、．]\s)', md_text)
                results = []
                for idx, part in enumerate(parts):
                    part = part.strip()
                    if not part: continue
                    title_match = re.match(r'^(\d+[\.\、．].*?)[\n\s]', part)
                    title = title_match.group(1) if title_match else f"题目 {idx + 1}"
                    
                    part = clean_latex(part)
                    
                    results.append({
                        "temp_id": str(idx + 1),
                        "title": title,
                        "description": part.replace('\n', '<br/>'),
                        "tags": ["AI识别", "GLM-OCR"]
                    })
                if not results:
                     return [{"temp_id": "1", "title": "GLM-OCR 识别", "description": clean_latex(md_text).replace('\n', '<br/>'), "tags": ["AI识别"]}]
                return results
            except Exception as e:
                print(f"[GLM-OCR ERROR] {str(e)}")
                raise HTTPException(status_code=500, detail=f"GLM-OCR 请求异常: {str(e)}")

    # ==========================================
    # 分支 2：通用大模型（GLM-4V 等）
    # ==========================================
    if not base_url or not base_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Base URL 配置错误")

    user_instruction = """请识别图中的题目并返回 JSON 数组。
1. 按大题号切分。(1)(2)小问放在同一个 description 里，用 <br/> 隔开。
2. 所有数学公式必须用 $ 包裹。
3. 返回的 JSON 格式： [{"title": "14.", "description": "（1）...<br/>（2）..."}]"""

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": OCR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_instruction},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                ]
            }
        ],
        "temperature": 0.1
    }

    max_retries = 2
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=f"AI服务器返回错误: {resp.text}")
                
                res_data = resp.json()
                
                if "choices" not in res_data or not res_data["choices"]:
                    raise HTTPException(status_code=500, detail=f"模型返回格式异常，无choices: {str(res_data)[:100]}")
                    
                content = res_data["choices"][0]["message"]["content"]
                print(f"\n========== [LLM OCR 原始返回] ==========\n{content}\n========================================\n")
                
                json_match = re.search(r'\[[\s\S]*\]', content)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = content.strip().removeprefix("```json").removesuffix("```").strip()

                json_str = fix_json_latex(json_str)

                try:
                    parsed_problems = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"[LLM OCR] JSON 解析失败: {e}\n原始字符串: {json_str}")
                    try:
                        fixed_json_str = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', json_str)
                        parsed_problems = json.loads(fixed_json_str)
                    except Exception as e2:
                        raise HTTPException(status_code=500, detail=f"AI 返回内容无法解析为 JSON: {str(e2)}")

                if not isinstance(parsed_problems, list):
                    raise HTTPException(status_code=500, detail="AI 返回的不是 JSON 数组格式")

                merged_results = []
                for p in parsed_problems:
                    if not isinstance(p, dict):
                        continue
                        
                    title = str(p.get("title", "")).strip()
                    desc = str(p.get("description", ""))
                    
                    # 【应用核心清洗】
                    desc = clean_latex(desc)

                    is_subquestion = re.match(r'^[\(（]\d+[\)）]', title) or re.match(r'^\d+[\.\、]\s*[\(（]\d+[\)）]', title)
                    if is_subquestion and merged_results:
                        merged_results[-1]["description"] += f"<br/>\n{title} {desc}"
                    else:
                        clean_title = re.sub(r'[\(（]\d+[\)）].*', '', title).strip()
                        if not clean_title: clean_title = title
                        merged_results.append({
                            "title": clean_title,
                            "description": f"{title} {desc}" if title not in desc else desc
                        })

                return [{
                    "temp_id": str(idx + 1),
                    "title": p.get("title", f"题目 {idx + 1}"),
                    "description": p.get("description", ""),
                    "tags": ["AI识别"]
                } for idx, p in enumerate(merged_results)]

        except HTTPException:
            raise
        except httpx.RequestError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            raise HTTPException(status_code=502, detail=f"网络连接失败: {str(e)}")
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            raise HTTPException(status_code=500, detail=f"请求异常: {str(e)}")