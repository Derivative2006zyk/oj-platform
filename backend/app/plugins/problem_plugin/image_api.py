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
    _: str = Depends(verify_admin_key),
):
    """
    上传图片（管理员），可选关联题目。
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

    # 保存文件
    ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    date_dir = datetime.now().strftime("%Y/%m")
    upload_dir = os.path.join(settings.UPLOAD_DIR, date_dir)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # 数据库只存文件名（相对路径），读取时拼接目录
    image = Image(
        problem_id=problem_id,
        file_name=file.filename,
        file_path=unique_name,   # 只存文件名
        file_size=len(content),
        mime_type=file.content_type,
        upload_by="admin",
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return {"id": image.id, "url": f"/api/images/{image.id}"}


@router.get("/images/{image_id}")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    """
    根据图片 ID 获取图片文件。
    兼容三种 file_path 格式：
      1. 绝对路径（Windows 或 Linux）
      2. 相对路径包含目录（如 2026/09/xxx.png）
      3. 只有文件名（如 xxx.png）
    """
    image = await db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    path = image.file_path

    # 1. 绝对路径：直接使用
    if os.path.isabs(path) and os.path.exists(path):
        return FileResponse(path, media_type=image.mime_type)

    # 2. 尝试相对路径拼接 UPLOAD_DIR（如 2026/09/xxx.png）
    candidate = os.path.join(settings.UPLOAD_DIR, path)
    if os.path.exists(candidate):
        return FileResponse(candidate, media_type=image.mime_type)

    # 3. 只存了文件名，扫描 uploads 下的年/月子目录查找
    for root, dirs, files in os.walk(settings.UPLOAD_DIR):
        if path in files:
            full = os.path.join(root, path)
            return FileResponse(full, media_type=image.mime_type)

    raise HTTPException(status_code=404, detail="图片文件已丢失")


@router.get("/image/{image_id}")
async def get_image_legacy(image_id: int, db: AsyncSession = Depends(get_db)):
    """兼容旧 URL（单数）"""
    return await get_image(image_id, db)


from fastapi import UploadFile, File, Depends, HTTPException, status as http_status
from app.core.security import get_current_user
from app.models.user import User


@router.post(
    "/images/upload",
    status_code=http_status.HTTP_201_CREATED,
)
async def upload_user_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """登录用户上传图片，用于证明题提交等场景。"""
    # 校验类型
    allowed = {"image/png", "image/jpeg", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {file.content_type}",
        )

    # 校验大小（5MB）
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Image exceeds 5MB",
        )

    # 落盘
    import uuid
    from pathlib import Path
    from app.core.config import settings

    ext = Path(file.filename or "image.png").suffix or ".png"
    file_name = f"{uuid.uuid4().hex}{ext}"

    upload_dir = Path(settings.UPLOAD_DIR) / "submissions"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file_name
    file_path.write_bytes(content)

    # 写 images 表
    from app.models.image import Image

    img = Image(
        problem_id=None,
        file_name=file.filename or file_name,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
        upload_by=str(current_user.id),
    )
    db.add(img)
    await db.commit()
    await db.refresh(img)

    return {"id": img.id, "url": f"/api/images/{img.id}"}