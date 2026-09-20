from fastapi import APIRouter, Depends, HTTPException

from app.core.security import verify_admin_key
from app.core.plugin_registry import get_plugin_registry
from app.core.plugin_config_store import get_config, set_enabled


router = APIRouter(prefix="/api/admin/plugins", tags=["plugins"])


@router.get("")
async def list_plugins(_: str = Depends(verify_admin_key)):
    """列出所有插件及其启用状态。"""
    registry = get_plugin_registry()
    plugins = []
    for info in registry.list_plugins():
        name = info["name"]
        db_config = await get_config(name)
        plugins.append({
            "name": name,
            "version": info["version"],
            "dependencies": info["dependencies"],
            "enabled": db_config.enabled if db_config else True,
        })
    return plugins


@router.put("/{plugin_name}/enable")
async def enable_plugin(
    plugin_name: str,
    _: str = Depends(verify_admin_key),
):
    """启用某插件。"""
    registry = get_plugin_registry()
    try:
        await registry.enable(plugin_name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"name": plugin_name, "enabled": True}


@router.put("/{plugin_name}/disable")
async def disable_plugin(
    plugin_name: str,
    _: str = Depends(verify_admin_key),
):
    """禁用某插件。"""
    registry = get_plugin_registry()
    try:
        await registry.disable(plugin_name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"name": plugin_name, "enabled": False}