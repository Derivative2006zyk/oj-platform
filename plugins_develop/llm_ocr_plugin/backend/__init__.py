from app.core.plugin_base import Plugin
from app.core.plugin_registry import register_plugin

@register_plugin
class LlmOcrPlugin(Plugin):
    name = "llm_ocr_plugin"
    version = "0.3.0"
    dependencies = ["problem_plugin"]

    async def on_load(self) -> None:
        pass

    def get_routers(self):
        # 动态加载本目录下的 api.py
        import importlib.util
        import sys
        from pathlib import Path
        plugin_dir = Path(__file__).parent
        spec = importlib.util.spec_from_file_location("_ext_llm_ocr_api", plugin_dir / "api.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_ext_llm_ocr_api"] = mod
        spec.loader.exec_module(mod)
        return [mod.router]