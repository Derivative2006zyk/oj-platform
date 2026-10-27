from app.core.plugin_base import Plugin
from app.core.plugin_registry import register_plugin


@register_plugin
class OcrPlugin(Plugin):
    name = "ocr_plugin"
    version = "0.3.0"
    dependencies = ["problem_plugin"]

    async def on_load(self) -> None:
        pass

    def get_routers(self):
        from app.plugins.ocr_plugin.api import router
        from app.plugins.ocr_plugin.batch_api import router as batch_router
        return [router, batch_router]