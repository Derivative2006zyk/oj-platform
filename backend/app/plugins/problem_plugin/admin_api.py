from fastapi import APIRouter, Depends
from app.core.security import verify_admin_key
from app.core.plugin_registry import get_plugin_registry
from app.core.plugin_config_store import get_config, set_enabled, update_config
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# 【核心修复】引入数据库依赖
from app.database import get_db
from app.schemas.problem import ProblemCreate
from app.plugins.problem_plugin.service import create_problem

# 【核心修复】将 prefix 置空，下面手写绝对路径，避免路由拼接混乱
router = APIRouter(prefix="", tags=["admin"])


# ===== 插件管理 =====

@router.get("/api/admin/plugins")
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


@router.put("/api/admin/plugins/{plugin_name}/enable")
async def enable_plugin(
    plugin_name: str,
    _: str = Depends(verify_admin_key),
):
    await set_enabled(plugin_name, True)
    registry = get_plugin_registry()
    if registry.get(plugin_name):
        await registry.enable(plugin_name)
    return {"name": plugin_name, "enabled": True}


@router.put("/api/admin/plugins/{plugin_name}/disable")
async def disable_plugin(
    plugin_name: str,
    _: str = Depends(verify_admin_key),
):
    await set_enabled(plugin_name, False)
    registry = get_plugin_registry()
    if registry.get(plugin_name):
        await registry.disable(plugin_name)
    return {"name": plugin_name, "enabled": False}


class PluginConfigUpdate(BaseModel):
    config: dict


@router.put("/api/admin/plugins/{plugin_name}/config")
async def update_plugin_config(
    plugin_name: str,
    data: PluginConfigUpdate,
    _: str = Depends(verify_admin_key),
):
    """更新插件的附加配置"""
    await update_config(plugin_name, data.config)
    return {"name": plugin_name, "config": data.config}


# ===== 题目批量导入 =====

class BatchImportItem(ProblemCreate):
    pass


class BatchImportRequest(BaseModel):
    problems: List[BatchImportItem]


@router.post("/api/admin/problems/batch")
async def batch_import_problems(
    req: BatchImportRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    """批量导入题目，用于 OCR 识别后入库"""
    imported = 0
    for item in req.problems:
        await create_problem(db, item)
        imported += 1
    return {"message": "success", "imported": imported}