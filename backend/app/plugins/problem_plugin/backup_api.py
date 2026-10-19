import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_admin_key
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["backup"])

@router.get("/admin/backup/export")
async def export_backup(_: str = Depends(verify_admin_key)):
    """导出完整备份（数据库 + 图片）为 ZIP"""
    tmp_dir = Path(tempfile.mkdtemp())
    sql_file = tmp_dir / "database.sql"
    zip_path = tmp_dir / "oj_backup.zip"

    # 1. 导出数据库
    env = os.environ.copy()
    env["PGPASSWORD"] = "oj_password"
    
    dump_cmd = [
        "pg_dump", "-h", "postgres", "-U", "oj", "-d", "oj_platform",
        "-f", str(sql_file)
    ]
    
    try:
        subprocess.run(dump_cmd, env=env, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"数据库导出失败: {e.stderr.decode()}")

    # 2. 打包数据库和图片
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(sql_file, "database.sql")
        
        upload_dir = Path(settings.UPLOAD_DIR)
        if upload_dir.exists():
            for file_path in upload_dir.rglob("*"):
                if file_path.is_file():
                    # 在 zip 内保持相对路径，例如 uploads/2026/10/xxx.png
                    arcname = Path("uploads") / file_path.relative_to(upload_dir)
                    zf.write(file_path, arcname)

    return FileResponse(
        path=zip_path,
        filename="oj_backup.zip",
        media_type="application/zip",
        background=None  # 注意：FastAPI 会在后台发送完后清理，如果需要立即清理需要写 BackgroundTask
    )


@router.post("/admin/backup/import")
async def import_backup(
    file: UploadFile = File(...),
    _: str = Depends(verify_admin_key)
):
    """从 ZIP 恢复数据"""
    tmp_dir = Path(tempfile.mkdtemp())
    zip_path = tmp_dir / "upload.zip"
    
    try:
        # 保存上传的 zip
        with open(zip_path, "wb") as f:
            f.write(await file.read())

        # 解压
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmp_dir)

        sql_file = tmp_dir / "database.sql"
        if not sql_file.exists():
            raise HTTPException(status_code=400, detail="备份文件中缺少 database.sql")

        # 1. 恢复数据库（先 drop 现有表）
        env = os.environ.copy()
        env["PGPASSWORD"] = "oj_password"
        
        # 警告：这会清空所有现有数据
        drop_cmd = [
            "psql", "-h", "postgres", "-U", "oj", "-d", "oj_platform",
            "-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
        ]
        subprocess.run(drop_cmd, env=env, check=True, capture_output=True)

        # 导入 SQL
        restore_cmd = [
            "psql", "-h", "postgres", "-U", "oj", "-d", "oj_platform",
            "-f", str(sql_file)
        ]
        subprocess.run(restore_cmd, env=env, check=True, capture_output=True)

        # 2. 恢复图片
        upload_zip_dir = tmp_dir / "uploads"
        if upload_zip_dir.exists():
            upload_dir = Path(settings.UPLOAD_DIR)
            # 清空旧图片（可选，这里为了安全不清空，直接覆盖）
            # shutil.rmtree(upload_dir, ignore_errors=True)
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 遍历覆盖
            for file_path in upload_zip_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(upload_zip_dir)
                    dest = upload_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest)

        return {"status": "ok", "message": "数据恢复成功，请重启后端容器使缓存失效"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)