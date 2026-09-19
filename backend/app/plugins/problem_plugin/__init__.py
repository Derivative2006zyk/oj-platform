from fastapi import APIRouter

from app.core.plugin_base import Plugin
from app.core.plugin_registry import register_plugin
from app.core.events import EventNames


@register_plugin
class ProblemPlugin(Plugin):
    name = "problem_plugin"
    version = "0.2.0"
    dependencies = []

    async def on_load(self) -> None:
        # 订阅问题事件（今天只订阅，不发布）
        from app.core.event_bus import get_event_bus
        bus = get_event_bus()
        bus.subscribe(EventNames.PROBLEM_CREATED, self._on_problem_created)
        bus.subscribe(EventNames.PROBLEM_UPDATED, self._on_problem_updated)
        bus.subscribe(EventNames.PROBLEM_DELETED, self._on_problem_deleted)

    def get_routers(self):
        from app.plugins.problem_plugin.api import router as problem_router
        from app.plugins.problem_plugin.image_api import router as image_router
        return [problem_router, image_router]

    # ===== 事件处理器 =====

    async def _on_problem_created(self, payload: dict) -> None:
        print(f"[problem_plugin] problem created: {payload}")

    async def _on_problem_updated(self, payload: dict) -> None:
        print(f"[problem_plugin] problem updated: {payload}")

    async def _on_problem_deleted(self, payload: dict) -> None:
        print(f"[problem_plugin] problem deleted: {payload}")