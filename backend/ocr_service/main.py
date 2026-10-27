from fastapi import FastAPI, UploadFile, File, HTTPException
from paddleocr import PaddleOCR
import numpy as np
import cv2
import io

app = FastAPI(title="OJ OCR Service")

# 初始化 PaddleOCR（自动下载轻量级中英文模型）
# 首次启动时会下载模型（约 20MB），可能需要一点时间
ocr_engine = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)

@app.post("/ocr")
async def process_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        # 调用 PaddleOCR 进行识别
        result = ocr_engine.ocr(img, cls=True)
        
        # 整理识别结果
        extracted_texts = []
        if result and result[0]:
            for line in result[0]:
                # line 结构: [ [[x1,y1],[x2,y2],...], (text, confidence) ]
                box = line[0]
                text = line[1][0]
                confidence = line[1][1]
                
                # 过滤掉置信度太低的结果
                if confidence > 0.6:
                    extracted_texts.append({
                        "text": text,
                        "box": box,
                        "confidence": float(confidence)
                    })

        return {
            "status": "success",
            "text_count": len(extracted_texts),
            "results": extracted_texts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))