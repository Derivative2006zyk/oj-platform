from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from fastapi import APIRouter


class Plugin(ABC):
    """插件抽象基类"""

    # ===== 元数据 =====
    name: str = ""
    version: str = "0.0.0"
    dependencies: List[str] = []

    # ===== 生命周期 =====

    @abstractmethod
    async def on_load(self) -> None:
        """插件加载时调用（注册路由、订阅事件）"""
        ...

    async def on_enable(self) -> None:
        """插件启用时调用"""
        pass

    async def on_disable(self) -> None:
        """插件禁用时调用"""
        pass

    async def on_unload(self) -> None:
        """插件卸载时调用"""
        pass

    async def on_install(self, plugin_dir: Path) -> None:
        """插件安装时调用（可选，用于拉起微服务）

        Args:
            plugin_dir: 插件解压后的根目录（包含 manifest.json）
        """
        pass

    async def on_uninstall(self, plugin_dir: Path) -> None:
        """插件卸载前调用（可选，用于销毁微服务）

        Args:
            plugin_dir: 插件根目录
        """
        pass

    # ===== 路由 =====

    def get_routers(self) -> List[APIRouter]:
        """返回该插件提供的 FastAPI 路由列表"""
        return []