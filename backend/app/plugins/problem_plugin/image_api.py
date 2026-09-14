# backend/app/plugins/problem_plugin/image_api.py

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

router = APIRouter(prefix="/api", tags=["images"])

# 允许的图片 MIME 类型
ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"]
# 不支持图片的题型
BLOCKED_PROBLEM_TYPES = ["choice", "fill_blank"]


async def get_db():
    async with async_session() as session:
        yield session


@router.post("/admin/images", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    problem_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    """
    上传图片（管理员），可选关联题目。
    - 校验类型、大小、有效性
    - 若关联题目，检查题型是否允许
    """
    # 1. 校验文件类型
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="仅支持PNG/JPEG/WebP格式")

    # 2. 读取文件内容，校验大小
    content = await file.read()
    if len(content) > settings.MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")

    # 3. 校验有效性（Pillow）
    try:
        img = PILImage.open(file.file)
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="无效的图片文件")
    finally:
        file.file.seek(0)

    # 4. 若关联题目，检查题型
    if problem_id is not None:
        problem = await db.get(Problem, problem_id)
        if not problem:
            raise HTTPException(status_code=404, detail="题目不存在")
        if problem.type in BLOCKED_PROBLEM_TYPES:
            raise HTTPException(status_code=400, detail="选择题和填空题不支持图片")

    # 5. 生成唯一文件名并按日期分目录
    ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    date_dir = datetime.now().strftime("%Y/%m")
    upload_dir = os.path.join(settings.UPLOAD_DIR, date_dir)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_name)

    # 6. 保存文件到磁盘
    with open(file_path, "wb") as f:
        f.write(content)

    # 7. 插入数据库记录
    image = Image(
        problem_id=problem_id,
        file_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        upload_by="admin",
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    # 8. 返回图片 ID 和访问 URL（注意路径必须是复数 images）
    return {
        "id": image.id,
        "url": f"/api/images/{image.id}"
    }


@router.get("/images/{image_id}")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    """根据图片 ID 获取图片文件（正式路由，复数）"""
    image = await db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    if not os.path.exists(image.file_path):
        raise HTTPException(status_code=404, detail="图片文件已丢失")
    return FileResponse(image.file_path, media_type=image.mime_type)


# 兼容旧 URL（单数），历史数据或缓存可能引用 /api/image/{id}
@router.get("/image/{image_id}")
async def get_image_legacy(image_id: int, db: AsyncSession = Depends(get_db)):
    """兼容旧 URL 的图片访问接口（单数）"""
    return await get_image(image_id, db)