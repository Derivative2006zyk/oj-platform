import importlib
import importlib.util
import pkgutil
import sys
from typing import Dict, List, Type
from pathlib import Path
from fastapi import APIRouter

from app.core.plugin_base import Plugin

# 全局变量，用于收集被 @register_plugin 装饰的类
_plugin_classes: List[Type[Plugin]] = []
_registry_instance = None

def register_plugin(cls: Type[Plugin]) -> Type[Plugin]:
    """装饰器：标记一个类为插件，并将其加入全局列表"""
    if not issubclass(cls, Plugin):
        raise TypeError(f"{cls} is not a subclass of Plugin")
    _plugin_classes.append(cls)
    return cls


class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}

    def discover(self, package: str) -> None:
        """扫描内置插件 (app.plugins)"""
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
        """扫描外部插件目录 (/app/plugins_installed)"""
        path = Path(plugin_dir)
        if not path.exists():
            return
            
        for item in path.iterdir():
            if item.is_dir():
                manifest_file = item / "manifest.json"
                entry_file = item / "backend" / "__init__.py"
                
                if manifest_file.exists() and entry_file.exists():
                    plugin_name = item.name
                    print(f"[PluginRegistry] Found external plugin: {plugin_name}")
                    
                    # 动态加载外部模块
                    try:
                        # 注意：这里需要给模块一个唯一的名称
                        mod_name = f"ext_plugin_{plugin_name}"
                        spec = importlib.util.spec_from_file_location(mod_name, entry_file)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[mod_name] = module
                        spec.loader.exec_module(module)
                    except Exception as e:
                        print(f"[PluginRegistry] Failed to load external plugin {plugin_name}: {e}")

    def _build_instances(self) -> None:
        """将全局列表中收集到的类实例化，存入 _plugins 字典"""
        for cls in _plugin_classes:
            try:
                instance = cls()
                self._plugins[instance.name] = instance
            except Exception as e:
                print(f"[PluginRegistry] Error instantiating {cls.__name__}: {e}")

    async def load_all(self) -> None:
        """加载所有插件（暂不实现复杂拓扑排序，直接遍历）"""
        for name, plugin in self._plugins.items():
            try:
                await plugin.on_load()
                print(f"[PluginRegistry] loaded: {name} v{plugin.version}")
            except Exception as e:
                print(f"[PluginRegistry] load error {name}: {e}")

    async def unload_all(self) -> None:
        for name, plugin in self._plugins.items():
            try:
                await plugin.on_unload()
            except Exception:
                pass

    async def enable(self, name: str) -> None:
        if name in self._plugins:
            await self._plugins[name].on_enable()

    async def disable(self, name: str) -> None:
        if name in self._plugins:
            await self._plugins[name].on_disable()

    def get(self, name: str) -> Plugin:
        return self._plugins.get(name)

    def list_plugins(self) -> List[Dict[str, str]]:
        return [
            {"name": p.name, "version": p.version, "dependencies": ",".join(p.dependencies)}
            for p in self._plugins.values()
        ]

    def collect_routers(self) -> List[APIRouter]:
        routers = []
        for plugin in self._plugins.values():
            routers.extend(plugin.get_routers())
        return routers


def get_plugin_registry() -> PluginRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PluginRegistry()
    return _registry_instance