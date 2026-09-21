# backend/app/plugins/user_plugin/__init__.py

from app.core.plugin_base import Plugin
from app.core.plugin_registry import register_plugin
from app.core.events import EventNames


@register_plugin
class UserPlugin(Plugin):
    name = "user_plugin"
    version = "0.2.0"
    dependencies = []

    async def on_load(self) -> None:
        from app.core.event_bus import get_event_bus
        bus = get_event_bus()
        bus.subscribe(EventNames.USER_REGISTERED, self._on_user_registered)
        bus.subscribe(EventNames.USER_LOGGED_IN, self._on_user_logged_in)

    def get_routers(self):
        from app.plugins.user_plugin.api import router as user_router
        return [user_router]

    async def _on_user_registered(self, payload: dict) -> None:
        print(f"[user_plugin] user registered: {payload}")

    async def _on_user_logged_in(self, payload: dict) -> None:
        print(f"[user_plugin] user logged in: {payload}")