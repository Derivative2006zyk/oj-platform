from typing import Dict, Optional

from sqlalchemy import select

from app.database import async_session
from app.models.plugin_config import PluginConfig


async def get_config(plugin_name: str) -> Optional[PluginConfig]:
    """读取一个插件的配置。不存在返回 None。"""
    async with async_session() as session:
        result = await session.execute(
            select(PluginConfig).where(PluginConfig.plugin_name == plugin_name)
        )
        return result.scalar_one_or_none()


async def get_all_configs() -> Dict[str, PluginConfig]:
    """读取全部插件配置，以 plugin_name 为键。"""
    async with async_session() as session:
        result = await session.execute(select(PluginConfig))
        rows = result.scalars().all()
    return {row.plugin_name: row for row in rows}


async def ensure_config(plugin_name: str, default_enabled: bool = True) -> PluginConfig:
    """确保插件有配置记录。不存在则创建。"""
    async with async_session() as session:
        result = await session.execute(
            select(PluginConfig).where(PluginConfig.plugin_name == plugin_name)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        new_config = PluginConfig(
            plugin_name=plugin_name,
            enabled=default_enabled,
            config={},
        )
        session.add(new_config)
        await session.commit()
        await session.refresh(new_config)
        return new_config


async def set_enabled(plugin_name: str, enabled: bool) -> PluginConfig:
    """更新插件的启用状态。不存在则创建。"""
    async with async_session() as session:
        result = await session.execute(
            select(PluginConfig).where(PluginConfig.plugin_name == plugin_name)
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            existing = PluginConfig(
                plugin_name=plugin_name,
                enabled=enabled,
                config={},
            )
            session.add(existing)
        else:
            existing.enabled = enabled

        await session.commit()
        await session.refresh(existing)
        return existing


async def update_config(plugin_name: str, config: dict) -> PluginConfig:
    """更新插件的 config 字段。"""
    async with async_session() as session:
        result = await session.execute(
            select(PluginConfig).where(PluginConfig.plugin_name == plugin_name)
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            existing = PluginConfig(
                plugin_name=plugin_name,
                enabled=True,
                config=config,
            )
            session.add(existing)
        else:
            existing.config = config

        await session.commit()
        await session.refresh(existing)
        return existing