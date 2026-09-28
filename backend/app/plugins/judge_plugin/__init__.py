from app.core.plugin_base import Plugin
from app.core.plugin_registry import register_plugin
from app.core.events import EventNames


@register_plugin
class JudgePlugin(Plugin):
    name = "judge_plugin"
    version = "0.2.0"
    dependencies = ["user_plugin", "problem_plugin"]

    async def on_load(self) -> None:
        from app.core.event_bus import get_event_bus
        bus = get_event_bus()
        bus.subscribe(EventNames.SUBMISSION_CREATED, self._on_submission_created)
        bus.subscribe(EventNames.SUBMISSION_JUDGED, self._on_submission_judged)

    def get_routers(self):
        from app.plugins.judge_plugin.api import router
        return [router]

    async def _on_submission_created(self, payload: dict) -> None:
        print(f"[judge_plugin] submission created: {payload}")

    async def _on_submission_judged(self, payload: dict) -> None:
        print(f"[judge_plugin] submission judged: {payload}")

        # 推送给该用户所有连接
        from app.core.ws_manager import get_ws_manager
        user_id = payload.get("user_id")
        if user_id is not None:
            manager = get_ws_manager()
            await manager.send_to_user(int(user_id), {
                "type": "judged",
                "submission_id": payload.get("id"),
                "status": payload.get("status"),
                "passed_cases": payload.get("passed_cases"),
                "total_cases": payload.get("total_cases"),
                "runtime_ms": payload.get("runtime_ms"),
            })