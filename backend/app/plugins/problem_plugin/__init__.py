from app.core.plugin_base import Plugin
from app.core.plugin_registry import register_plugin
from app.core.event_bus import get_event_bus
from app.core.ws_manager import get_ws_manager


@register_plugin
class ProblemPlugin(Plugin):
    name = "problem_plugin"
    version = "0.2.0"
    dependencies = []

    async def on_load(self) -> None:
        bus = get_event_bus()
        bus.subscribe("problem.created", self._broadcast_created)
        bus.subscribe("problem.updated", self._broadcast_updated)
        bus.subscribe("problem.deleted", self._broadcast_deleted)

    async def _broadcast_created(self, data: dict):
        await get_ws_manager().broadcast({"type": "problem.created", "data": data})

    async def _broadcast_updated(self, data: dict):
        await get_ws_manager().broadcast({"type": "problem.updated", "data": data})

    async def _broadcast_deleted(self, data: dict):
        await get_ws_manager().broadcast({"type": "problem.deleted", "data": data})

    def get_routers(self):
        from app.plugins.problem_plugin.api import router as api_router
        from app.plugins.problem_plugin.admin_api import router as admin_router
        from app.plugins.problem_plugin.image_api import router as image_router
        from app.plugins.problem_plugin.market_api import router as market_router
        
        # 【新增】导入 bank 相关的路由
        from app.plugins.problem_plugin.bank_api import router as bank_router
        from app.plugins.problem_plugin.bank_crud_api import router as bank_crud_router
        
        return [
            api_router, 
            admin_router, 
            image_router, 
            market_router,
            # 【新增】挂载 bank 路由
            bank_router,
            bank_crud_router,
        ]