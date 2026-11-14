from app.core.plugin_base import Plugin
from app.core.plugin_registry import register_plugin

@register_plugin
class AIPlugin(Plugin):
    name = "ai_plugin"
    version = "0.3.0"
    dependencies = []

    async def on_load(self) -> None:
        pass

    def get_routers(self):
        from app.plugins.ai_plugin.api import router
        return [router]