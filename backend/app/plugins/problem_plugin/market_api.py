import io
import shutil
import tempfile
import zipfile
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import require_admin
from app.core.plugin_registry import (
    get_plugin_registry,
    PLUGINS_INSTALLED_DIR,
)
from app.models.user import User

router = APIRouter(prefix="/api", tags=["market"])


class InstallRequest(BaseModel):
    download_url: str


@router.get("/market/plugins")
async def get_market_plugins():
    """插件市场列表（Day 49 已实现，保持不变）"""
    return [
        {
            "name": "ocr_plugin",
            "display_name": "数学 OCR 拍照录题",
            "version": "0.3.0",
            "author": "OJ Team",
            "description": "基于 PaddleOCR + pix2tex 的本地离线公式识别。安装后会拉起 GPU 微服务。",
            "download_url": "http://host.docker.internal:9000/ocr_plugin.ojplugin",
        },
    ]


@router.post("/admin/market/install")
async def install_plugin(
    req: InstallRequest,
    current_user: User = Depends(require_admin),
):
    """下载 → 解压 → pip install → on_install(拉微服务)"""
    # 1. 下载 ZIP
    tmp_zip = Path(tempfile.gettempdir()) / "plugin_download.zip"
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", req.download_url) as resp:
                resp.raise_for_status()
                with open(tmp_zip, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")

    # 2. 解压到 plugins_installed/{name}/（name 从 manifest.json 读）
    try:
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            # 找 manifest.json
            names = zf.namelist()
            manifest_name = next((n for n in names if n.endswith("manifest.json") and "/" not in n.rstrip("/")), None)
            if manifest_name is None:
                raise HTTPException(status_code=400, detail="manifest.json not found in package")
            import json
            manifest = json.loads(zf.read(manifest_name))
            plugin_name = manifest.get("name") or manifest.get("folder_name")
            if not plugin_name:
                raise HTTPException(status_code=400, detail="manifest.json missing 'name' field")

            target_dir = PLUGINS_INSTALLED_DIR / plugin_name
            if target_dir.exists():
                raise HTTPException(status_code=409, detail=f"Plugin '{plugin_name}' already installed")

            target_dir.mkdir(parents=True, exist_ok=True)
            zf.extractall(target_dir)
    except zipfile.BadZipFile as e:
        raise HTTPException(status_code=400, detail=f"Bad zip file: {e}")
    finally:
        tmp_zip.unlink(missing_ok=True)

    # 3. pip install 插件后端依赖
    req_file = target_dir / "backend" / "requirements.txt"
    if req_file.exists():
        import asyncio
        proc = await asyncio.create_subprocess_exec(
            "pip", "install", "--no-cache-dir", "-r", str(req_file),
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            # 清理已解压的文件，回滚
            shutil.rmtree(target_dir, ignore_errors=True)
            raise HTTPException(status_code=500, detail=f"pip install failed: {stderr.decode()[:500]}")

    # 4. 触发 on_install（拉起微服务）
    try:
        registry = get_plugin_registry()
        await registry.install_plugin(plugin_name)
    except Exception as e:
        # 保留文件方便手动排查，但告知失败
        raise HTTPException(status_code=500, detail=f"Plugin on_install failed: {e}")

    return {"status": "ok", "plugin_name": plugin_name}


@router.delete("/admin/market/uninstall/{plugin_name}")
async def uninstall_plugin(
    plugin_name: str,
    current_user: User = Depends(require_admin),
):
    """触发 on_uninstall + 删除目录"""
    target_dir = PLUGINS_INSTALLED_DIR / plugin_name
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not installed")

    registry = get_plugin_registry()
    try:
        await registry.uninstall_plugin(plugin_name)
    except Exception as e:
        print(f"[Market] uninstall hook error: {e}")

    shutil.rmtree(target_dir, ignore_errors=True)
    return {"status": "ok", "plugin_name": plugin_name}