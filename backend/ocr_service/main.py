from fastapi import FastAPI, UploadFile, File, HTTPException
from paddleocr import PaddleOCR
from pix2tex.cli import LatexOCR
import numpy as np
import cv2
from PIL import Image
import re
import torch

app = FastAPI(title="OJ OCR Service")

print(f"==== GPU 可用性: {torch.cuda.is_available()} ====")

ocr_engine = PaddleOCR(use_angle_cls=False, lang="ch", show_log=False, use_gpu=False)
latex_engine = LatexOCR()

def should_use_latex_model(text: str) -> bool:
    if not text: return False
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    if chinese_chars > 3: return False
    if text.isalpha() and chinese_chars == 0: return False
    math_symbols = ['=', '<', '>', '∈', '∑', '∫', '^', '_', '\\', '{', '}']
    if not any(sym in text for sym in math_symbols): return False
    return True

def fix_latex_braces(latex: str) -> str:
    """严格的容错：剔除出错的垃圾公式"""
    left_braces = latex.count('{')
    right_braces = latex.count('}')
    
    # 1. 如果大括号严重不匹配，直接丢弃
    if left_braces != right_braces:
        return ""
    
    # 2. 如果包含太多莫名其妙的标点（如连续的逗号），也丢弃
    if re.search(r'[,;]{3,}', latex):
        return ""
    
    # 3. 如果公式太短且全是标点符号，丢弃
    if len(latex) < 8 and not any(c.isalnum() for c in latex):
        return ""

    return latex

@app.post("/ocr")
async def process_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        h, w = img.shape[:2]
        if max(h, w) > 1200:
            scale = 1200 / max(h, w)
            img = cv2.resize(img, (int(w*scale), int(h*scale)))

        result = ocr_engine.ocr(img, cls=True)
        
        extracted_texts = []
        if result and result[0]:
            for line in result[0]:
                box = line[0]
                text = line[1][0]
                confidence = line[1][1]

                if should_use_latex_model(text):
                    pts = np.array(box, np.int32)
                    x, y, w_box, h_box = cv2.boundingRect(pts)
                    
                    if h_box > 150 or w_box > 600:
                        final_text = text
                    else:
                        crop = img[max(0, y-5):min(img.shape[0], y+h_box+5), max(0, x-5):min(img.shape[1], x+w_box+5)]
                        try:
                            latex = latex_engine(Image.fromarray(crop))
                            # 强制清洗
                            latex = fix_latex_braces(latex)
                            if not latex:
                                final_text = text
                            else:
                                final_text = f"$$\n{latex}\n$$"
                        except Exception:
                            final_text = text
                else:
                    final_text = text

                extracted_texts.append({
                    "text": final_text,
                    "box": box,
                    "confidence": float(confidence)
                })

        return {"status": "success", "text_count": len(extracted_texts), "results": extracted_texts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))