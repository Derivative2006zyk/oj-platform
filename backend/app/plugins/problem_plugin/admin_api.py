from fastapi import APIRouter, Depends
from app.core.security import verify_admin_key
from app.core.plugin_registry import get_plugin_registry
from app.core.plugin_config_store import get_config, set_enabled

router = APIRouter(prefix="/api/admin/plugins", tags=["plugins"])

@router.get("")
async def list_plugins(_: str = Depends(verify_admin_key)):
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
    # 无论如何，直接写库，重启即生效！
    await set_enabled(plugin_name, True)
    
    registry = get_plugin_registry()
    if registry.get(plugin_name):
        await registry.enable(plugin_name)
    return {"name": plugin_name, "enabled": True}

@router.put("/{plugin_name}/disable")
async def disable_plugin(
    plugin_name: str,
    _: str = Depends(verify_admin_key),
):
    # 无论如何，直接写库，重启即生效！
    await set_enabled(plugin_name, False)
    
    registry = get_plugin_registry()
    if registry.get(plugin_name):
        await registry.disable(plugin_name)
    return {"name": plugin_name, "enabled": False}

from pydantic import BaseModel
from app.core.plugin_config_store import update_config # 确保引入了 update_config

class PluginConfigUpdate(BaseModel):
    config: dict

@router.put("/{plugin_name}/config")
async def update_plugin_config(
    plugin_name: str,
    data: PluginConfigUpdate,
    _: str = Depends(verify_admin_key),
):
    """更新插件的附加配置"""
    await update_config(plugin_name, data.config)
    return {"name": plugin_name, "config": data.config}