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