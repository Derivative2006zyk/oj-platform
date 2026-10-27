from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import httpx

router = APIRouter(prefix="/api/plugins/ocr", tags=["ocr"])

# 注意：在 Docker Compose 中，服务名就是域名
OCR_SERVICE_URL = "http://ocr-service:8001/ocr"

@router.post("/parse")
async def parse_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            response = await client.post(OCR_SERVICE_URL, files=files)
            response.raise_for_status()
            ocr_data = response.json()
            
            # 将 PaddleOCR 的文本块合并成 Markdown 格式
            texts = [item["text"] for item in ocr_data.get("results", [])]
            raw_content = "\n\n".join(texts)

            return [{
                "temp_id": "1",
                "title": "拍照识别出的题目",
                "description": raw_content,
                "type": "algorithm", 
                "difficulty": 1,
                "tags": ["OCR识别"]
            }]
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"无法连接到本地 OCR 服务: {exc}")