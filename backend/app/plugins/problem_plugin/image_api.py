import uuid
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image as PILImage

from app.database import async_session
from app.models.problem import Problem
from app.models.image import Image
from app.core.config import settings
from app.core.security import verify_admin_key

router = APIRouter(prefix='/api', tags=['images'])

ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"]
BLOCKED_PROBLEM_TYPES = ["choice", "fill_blank"]

async def get_db():
    async with async_session() as session:
        yield session

@router.post("/admin/images", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    problem_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    上传图片（管理员），可选关联题目。
    - 校验类型、大小、有效性
    - 若关联题目，检查题型是否允许
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="仅支持PNG/JPEG/WebP格式")

    content = await file.read()
    if len(content) > settings.MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")
    try:
        img = PILImage.open(file.file)
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="无效的图片文件")
    finally:
        file.file.seek(0)

    if problem_id is not None:
        problem = await db.get(Problem, problem_id)
        if not problem:
            raise HTTPException(status_code=404, detail="题目不存在")
        if problem.type in BLOCKED_PROBLEM_TYPES:
            raise HTTPException(status_code=400, detail="选择题和填空题不支持图片")

    ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    date_dir = datetime.now().strftime("%Y/%m")
    upload_dir = os.path.join(settings.UPLOAD_DIR, date_dir)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    image = Image(
        problem_id=problem_id,
        file_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        upload_by="admin"
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return {
        "id": image.id,
        "url": f"/api/image/{image.id}"
    }

@router.get("/images/{image_id}")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    """根据图片ID获取图片文件"""
    image = await db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    if not os.path.exists(image.file_path):
        raise HTTPException(status_code=404, detail="图片文件已丢失")
    return FileResponse(image.file_path, media_type=image.mime_type)