from fastapi import APIRouter, UploadFile, File, Query, HTTPException
import httpx
import re

router = APIRouter(prefix="/api/plugins/ocr", tags=["ocr"])

OCR_SERVICE_URL = "http://ocr-service:8001/ocr"

def clean_to_latex(text: str) -> str:
    """用正则暴力清洗 PaddleOCR 的常见错误，转为 LaTeX"""
    # 修复常见的绝对值符号 (例如把 |x| 识别成 1x1)
    text = re.sub(r'1([a-zA-Z]+)1', r'|\1|', text)
    # 修复 lim 极限符号
    text = text.replace("lim", "\\lim ")
    # 修复数列 x_n
    text = re.sub(r'xn', 'x_n', text)
    # 如果整行没有 $，就包裹起来
    if "\\" in text or "lim" in text or "diam" in text:
        if not text.startswith("$"):
            text = f"$$\n{text}\n$$"
    return text

@router.post("/parse")
async def parse_image(
    file: UploadFile = File(...),
    problem_type: str = Query("algorithm", alias="type")
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            response = await client.post(OCR_SERVICE_URL, files=files)
            response.raise_for_status()
            ocr_data = response.json()
            
            # 将 PaddleOCR 的文本块清洗并合并
            texts = [clean_to_latex(item["text"]) for item in ocr_data.get("results", [])]
            raw_content = "\n\n".join(texts)

            return [{
                "temp_id": "1",
                "title": "拍照识别出的题目",
                "description": raw_content,
                "type": problem_type, # 使用前端传来的题型
                "difficulty": 1,
                "tags": ["OCR识别"]
            }]
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"无法连接到本地 OCR 服务: {exc}")