import json
import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path
from typing import Dict, List, Type

from fastapi import APIRouter

from app.core.plugin_base import Plugin

_plugin_classes: List[Type[Plugin]] = []
_registry_instance = None

PLUGINS_INSTALLED_DIR = Path("/app/plugins_installed")


def register_plugin(cls: Type[Plugin]) -> Type[Plugin]:
    if not issubclass(cls, Plugin):
        raise TypeError(f"{cls} is not a subclass of Plugin")
    if cls not in _plugin_classes:
        _plugin_classes.append(cls)
    return cls


class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}

    def discover(self, package: str) -> None:
        try:
            mod = importlib.import_module(package)
            for _, name, _ in pkgutil.iter_modules(mod.__path__):
                module_name = f"{package}.{name}"
                try:
                    importlib.import_module(module_name)
                except Exception as e:
                    print(f"[PluginRegistry] Error loading {module_name}: {e}")
        except Exception as e:
            print(f"[PluginRegistry] Error discovering {package}: {e}")

    def discover_external(self, plugin_dir: str) -> None:
        path = Path(plugin_dir)
        if not path.exists():
            return
        for item in path.iterdir():
            if not item.is_dir(): continue
            manifest_file = item / "manifest.json"
            entry_file = item / "backend" / "__init__.py"
            if not (manifest_file.exists() and entry_file.exists()): continue

            plugin_name = item.name
            mod_name = f"ext_plugin_{plugin_name}"
            if mod_name in sys.modules: continue

            print(f"[PluginRegistry] Found external plugin: {plugin_name}")
            try:
                before_classes = set(_plugin_classes)
                spec = importlib.util.spec_from_file_location(mod_name, entry_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
                for cls in _plugin_classes:
                    if cls not in before_classes:
                        if cls.name != plugin_name:
                            print(f"[PluginRegistry] Correcting plugin name: {cls.name} -> {plugin_name}")
                            cls.name = plugin_name
            except Exception as e:
                print(f"[PluginRegistry] Failed to load external plugin {plugin_name}: {e}")

    def reload_external(self, plugin_dir: str) -> None:
        self.discover_external(plugin_dir)
        self._build_instances()

    def _build_instances(self) -> None:
        for cls in _plugin_classes:
            try:
                instance = cls()
                if instance.name not in self._plugins:
                    self._plugins[instance.name] = instance
            except Exception as e:
                print(f"[PluginRegistry] Error instantiating {cls.__name__}: {e}")

    async def load_all(self) -> None:
        from app.core.plugin_config_store import get_all_configs
        configs = await get_all_configs()
        for name, plugin in self._plugins.items():
            enabled = configs[name].enabled if name in configs else True
            plugin._enabled = enabled
            if not enabled:
                print(f"[PluginRegistry] skip disabled plugin: {name}")
                continue
            try:
                await plugin.on_load()
                print(f"[PluginRegistry] loaded: {name} v{plugin.version}")
            except Exception as e:
                print(f"[PluginRegistry] load error {name}: {e}")

    async def unload_all(self) -> None:
        for name, plugin in self._plugins.items():
            try: await plugin.on_unload()
            except Exception: pass

    async def enable(self, name: str) -> None:
        if name in self._plugins:
            self._plugins[name]._enabled = True
            await self._plugins[name].on_enable()

    async def disable(self, name: str) -> None:
        if name in self._plugins:
            self._plugins[name]._enabled = False
            await self._plugins[name].on_disable()

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    def list_plugins(self) -> List[Dict[str, str]]:
        return [{"name": p.name, "version": p.version, "dependencies": ",".join(p.dependencies)} for p in self._plugins.values()]

    def collect_routers(self) -> List[APIRouter]:
        routers = []
        for name, plugin in self._plugins.items():
            if getattr(plugin, "_enabled", True) is False: continue
            routers.extend(plugin.get_routers())
        return routers

    async def get_ui_manifests(self) -> List[dict]:
        from app.core.plugin_config_store import get_all_configs
        configs = await get_all_configs()

        results = []
        path = PLUGINS_INSTALLED_DIR
        if not path.exists(): return results

        for item in path.iterdir():
            if item.is_dir():
                manifest_file = item / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            data["folder_name"] = item.name
                            data["name"] = item.name
                            
                            db_cfg = configs.get(item.name)
                            data["enabled"] = db_cfg.enabled if db_cfg else True
                            
                            # 【核心修复】完整返回 config 字典
                            plugin_config = db_cfg.config if db_cfg and db_cfg.config else {}
                            data["show_in_nav"] = plugin_config.get("show_in_nav", True)
                            data["config"] = plugin_config
                            
                            results.append(data)
                    except Exception as e:
                        print(f"[PluginRegistry] Error reading manifest {item.name}: {e}")
        return results

    async def install_plugin(self, name: str) -> None:
        self.reload_external(str(PLUGINS_INSTALLED_DIR))
        plugin = self._plugins.get(name)
        if plugin is None:
            raise RuntimeError(f"Plugin class for '{name}' not found after reload")

        from app.core.plugin_config_store import ensure_config
        await ensure_config(name, default_enabled=True)
        plugin._enabled = True
        await plugin.on_install(PLUGINS_INSTALLED_DIR / name)

    async def uninstall_plugin(self, name: str) -> None:
        plugin = self._plugins.get(name)
        plugin_dir = PLUGINS_INSTALLED_DIR / name
        if plugin is not None:
            try:
                await plugin.on_uninstall(plugin_dir)
            finally:
                try: await plugin.on_unload()
                except Exception: pass
                self._plugins.pop(name, None)

        compose_file = plugin_dir / "docker-compose.yml"
        if compose_file.exists():
            import asyncio
            try:
                proc = await asyncio.create_subprocess_exec(
                    "docker", "compose", "-p", f"oj-plugin-{name}", "-f", str(compose_file), "down", "--remove-orphans",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
            except Exception as e:
                print(f"[PluginRegistry] compose down failed: {e}")

def get_plugin_registry() -> PluginRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PluginRegistry()
    return _registry_instance