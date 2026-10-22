import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import verify_admin_key

router = APIRouter(prefix="/api", tags=["market"])

PLUGINS_DIR = Path("/app/plugins_installed")

class InstallRequest(BaseModel):
    download_url: str

@router.post("/admin/market/install")
async def install_plugin(
    req: InstallRequest,
    _: str = Depends(verify_admin_key)
):
    """从指定 URL 下载并安装 .ojplugin (ZIP) 插件"""
    url = req.download_url
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid download URL")

    # 1. 下载 ZIP
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            zip_data = resp.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"下载失败: {str(e)}")

    # 2. 安全解压
    tmp_dir = Path(tempfile.mkdtemp())
    zip_path = tmp_dir / "plugin.zip"
    zip_path.write_bytes(zip_data)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # 防止 Zip Slip 路径穿越攻击
            for member in zf.infolist():
                target_path = (tmp_dir / member.filename).resolve()
                if not str(target_path).startswith(str(tmp_dir.resolve())):
                    raise HTTPException(status_code=400, detail="ZIP 包含恶意路径")
            zf.extractall(tmp_dir)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="上传的文件不是有效的 ZIP")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解压失败: {str(e)}")

    # 3. 校验 manifest.json
    # 允许 ZIP 内有一层文件夹，或者直接在根目录
    manifest_file = tmp_dir / "manifest.json"
    source_dir = tmp_dir
    
    if not manifest_file.exists():
        # 尝试找一级子目录
        subdirs = [d for d in tmp_dir.iterdir() if d.is_dir()]
        if len(subdirs) == 1 and (subdirs[0] / "manifest.json").exists():
            source_dir = subdirs[0]
            manifest_file = source_dir / "manifest.json"
        else:
            raise HTTPException(status_code=400, detail="无效的插件包：缺少 manifest.json")

    # 4. 移动文件到 plugins_installed 目录
    import json
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        plugin_name = manifest.get("name")
        if not plugin_name:
            raise HTTPException(status_code=400, detail="manifest.json 缺少 name 字段")

    target_plugin_dir = PLUGINS_DIR / plugin_name
    if target_plugin_dir.exists():
        # 覆盖安装：直接删除旧版
        shutil.rmtree(target_plugin_dir)

    try:
        # 将 source_dir 的内容复制到 target_plugin_dir
        shutil.copytree(source_dir, target_plugin_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入插件目录失败: {str(e)}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return {
        "status": "ok",
        "message": f"插件 {plugin_name} 安装成功，请重启应用以加载新插件。",
        "need_restart": True
    }