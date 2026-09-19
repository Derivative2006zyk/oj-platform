from abc import ABC, abstractmethod
from typing import List

from fastapi import APIRouter


class Plugin(ABC):
    """插件抽象基类。所有业务插件必须继承此类。

    项目总览 9.2 节定义的生命周期：
    - on_load:    加载时调用（注册路由、订阅事件）
    - on_enable:  启用时调用
    - on_disable: 禁用时调用
    - on_unload:  卸载时调用（释放资源）
    """

    name: str = ""
    version: str = "0.0.0"
    dependencies: List[str] = []

    def get_routers(self) -> List[APIRouter]:
        """返回该插件要挂载的路由列表。默认空。"""
        return []

    @abstractmethod
    async def on_load(self) -> None:
        """加载阶段。注册路由、订阅事件、初始化资源。"""

    async def on_enable(self) -> None:
        """启用阶段。默认无操作。"""

    async def on_disable(self) -> None:
        """禁用阶段。默认无操作。"""

    async def on_unload(self) -> None:
        """卸载阶段。释放资源、注销事件。默认无操作。"""