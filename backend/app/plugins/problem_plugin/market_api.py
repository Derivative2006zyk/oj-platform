import asyncio
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

# 内存字典，记录安装进度
_install_status = {}


class InstallRequest(BaseModel):
    download_url: str


@router.get("/market/plugins")
async def get_market_plugins():
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


@router.get("/admin/market/install_status/{plugin_name}")
async def get_install_status(plugin_name: str, current_user: User = Depends(require_admin)):
    """供前端轮询查询安装进度"""
    status = _install_status.get(plugin_name)
    if not status:
        return {"status": "unknown"}
    return status


async def _background_install(plugin_name: str, download_url: str):
    """后台异步执行下载、解压、pip install、on_install"""
    tmp_zip = Path(tempfile.gettempdir()) / f"plugin_{plugin_name}.zip"
    
    try:
        # 1. 下载
        _install_status[plugin_name] = {"status": "downloading"}
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", download_url) as resp:
                resp.raise_for_status()
                with open(tmp_zip, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)

        # 2. 解压
        _install_status[plugin_name] = {"status": "extracting"}
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            names = zf.namelist()
            manifest_name = next((n for n in names if n.endswith("manifest.json") and "/" not in n.rstrip("/")), None)
            if not manifest_name:
                raise Exception("Invalid package: manifest.json not found")
                
            import json
            manifest = json.loads(zf.read(manifest_name))
            real_name = manifest.get("name") or manifest.get("folder_name")
            if not real_name:
                raise Exception("Invalid package: missing 'name' field")
                
            target_dir = PLUGINS_INSTALLED_DIR / real_name
            if target_dir.exists():
                raise Exception(f"Plugin '{real_name}' already installed")

            target_dir.mkdir(parents=True, exist_ok=True)
            zf.extractall(target_dir)

        # 3. pip install
        req_file = target_dir / "backend" / "requirements.txt"
        if req_file.exists():
            _install_status[plugin_name] = {"status": "installing_deps"}
            proc = await asyncio.create_subprocess_exec(
                "pip", "install", "--no-cache-dir", "-r", str(req_file),
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                shutil.rmtree(target_dir, ignore_errors=True)
                raise Exception(f"pip install failed: {stderr.decode()[:500]}")

        # 4. 触发 on_install 拉起微服务
        _install_status[plugin_name] = {"status": "starting_service"}
        registry = get_plugin_registry()
        await registry.install_plugin(real_name)

        _install_status[plugin_name] = {"status": "success", "real_name": real_name}

    except Exception as e:
        _install_status[plugin_name] = {"status": "error", "detail": str(e)}
        # 如果失败，清理目录
        if (PLUGINS_INSTALLED_DIR / plugin_name).exists():
            shutil.rmtree(PLUGINS_INSTALLED_DIR / plugin_name, ignore_errors=True)
    finally:
        if tmp_zip.exists():
            tmp_zip.unlink()


@router.post("/admin/market/install")
async def install_plugin(
    req: InstallRequest,
    current_user: User = Depends(require_admin),
):
    """接收安装请求，立即返回，由后台协程处理"""
    # 简单根据 URL 解析名字，或者利用临时名字，最终重命名由 manifest 决定
    tmp_name = "ocr_plugin" # 为了简单，这里先硬编码，因为市场现在只有一个
    if _install_status.get(tmp_name, {}).get("status") in ["downloading", "extracting", "installing_deps", "starting_service"]:
        raise HTTPException(status_code=409, detail="Installation already in progress")
        
    _install_status[tmp_name] = {"status": "starting"}
    # 启动后台任务
    asyncio.create_task(_background_install(tmp_name, req.download_url))
    
    return {"status": "started"}


@router.delete("/admin/market/uninstall/{plugin_name}")
async def uninstall_plugin(
    plugin_name: str,
    current_user: User = Depends(require_admin),
):
    target_dir = PLUGINS_INSTALLED_DIR / plugin_name
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not installed")

    registry = get_plugin_registry()
    try:
        await registry.uninstall_plugin(plugin_name)
    except Exception as e:
        print(f"[Market] uninstall hook error: {e}")

    shutil.rmtree(target_dir, ignore_errors=True)
    _install_status.pop(plugin_name, None)
    return {"status": "ok", "plugin_name": plugin_name}