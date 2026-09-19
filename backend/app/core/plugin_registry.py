import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Type

from app.core.plugin_base import Plugin


class PluginRegistry:
    """插件注册表。

    项目总览 3.6.2 节：基座通过注册表发现和挂载插件。
    使用方式：
        registry = PluginRegistry()
        registry.discover("app.plugins")
        await registry.load_all()
        for router in registry.collect_routers():
            app.include_router(router)
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}
        self._loaded = False

    # ============ 注册 ============

    def register(self, plugin_cls: Type[Plugin]) -> Type[Plugin]:
        """注册一个插件类。由 @register_plugin 装饰器调用。"""
        if not plugin_cls.name:
            raise ValueError(
                f"Plugin {plugin_cls.__name__} must define a non-empty 'name'"
            )
        if plugin_cls.name in self._plugin_classes:
            existing = self._plugin_classes[plugin_cls.name]
            raise ValueError(
                f"Plugin name conflict: '{plugin_cls.name}' "
                f"already registered by {existing.__name__}"
            )
        self._plugin_classes[plugin_cls.name] = plugin_cls
        return plugin_cls

    # ============ 发现 ============

    def discover(self, package: str) -> None:
        """扫描指定包下所有模块，触发 @register_plugin 装饰器。

        参数 package 为 Python 包路径，如 "app.plugins"。
        """
        try:
            pkg = importlib.import_module(package)
        except ImportError as e:
            print(f"[PluginRegistry] cannot import package {package}: {e}")
            return

        if not hasattr(pkg, "__path__"):
            # 不是包，直接返回
            return

        for _, mod_name, _ in pkgutil.walk_packages(
            pkg.__path__, prefix=f"{package}."
        ):
            try:
                importlib.import_module(mod_name)
            except Exception as e:
                print(f"[PluginRegistry] failed to import {mod_name}: {e}")

    # ============ 实例化与生命周期 ============

    def _build_instances(self) -> None:
        """实例化所有已注册的插件类。"""
        for name, cls in self._plugin_classes.items():
            if name not in self._plugins:
                self._plugins[name] = cls()

    async def load_all(self) -> None:
        """依次加载并启用所有插件。"""
        if self._loaded:
            return

        self._build_instances()

        # 按依赖拓扑排序（简单实现：无依赖先加载）
        ordered = self._topological_order()

        for name in ordered:
            plugin = self._plugins[name]
            try:
                await plugin.on_load()
                await plugin.on_enable()
                print(f"[PluginRegistry] loaded: {name} v{plugin.version}")
            except Exception as e:
                print(f"[PluginRegistry] failed to load {name}: {e}")
                raise

        self._loaded = True

    async def unload_all(self) -> None:
        """逆序卸载所有插件。"""
        if not self._loaded:
            return

        ordered = self._topological_order()

        for name in reversed(ordered):
            plugin = self._plugins[name]
            try:
                await plugin.on_disable()
                await plugin.on_unload()
                print(f"[PluginRegistry] unloaded: {name}")
            except Exception as e:
                print(f"[PluginRegistry] failed to unload {name}: {e}")

        self._loaded = False

    async def enable(self, name: str) -> None:
        """单独启用某插件。"""
        plugin = self._plugins.get(name)
        if plugin is None:
            raise KeyError(f"Plugin not found: {name}")
        await plugin.on_enable()
        print(f"[PluginRegistry] enabled: {name}")

    async def disable(self, name: str) -> None:
        """单独禁用某插件。"""
        plugin = self._plugins.get(name)
        if plugin is None:
            raise KeyError(f"Plugin not found: {name}")
        await plugin.on_disable()
        print(f"[PluginRegistry] disabled: {name}")

    # ============ 查询 ============

    def get(self, name: str) -> Plugin:
        plugin = self._plugins.get(name)
        if plugin is None:
            raise KeyError(f"Plugin not found: {name}")
        return plugin

    def list_plugins(self) -> List[Dict[str, str]]:
        result = []
        for name, plugin in self._plugins.items():
            result.append({
                "name": name,
                "version": plugin.version,
                "dependencies": ",".join(plugin.dependencies),
            })
        return result

    def collect_routers(self):
        """收集所有插件的路由。"""
        routers = []
        for plugin in self._plugins.values():
            routers.extend(plugin.get_routers())
        return routers

    # ============ 内部 ============

    def _topological_order(self) -> List[str]:
        """按依赖拓扑排序。无依赖的插件先排。"""
        ordered: List[str] = []
        visited: set = set()

        def visit(name: str, stack: set) -> None:
            if name in visited:
                return
            if name in stack:
                raise ValueError(f"Circular dependency detected: {name}")
            stack.add(name)
            plugin = self._plugins.get(name)
            if plugin is None:
                raise KeyError(f"Dependency not found: {name}")
            for dep in plugin.dependencies:
                visit(dep, stack)
            stack.discard(name)
            visited.add(name)
            ordered.append(name)

        for name in self._plugins:
            visit(name, set())

        return ordered


# ===== 全局单例 =====

_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    """获取全局插件注册表单例（懒加载）。"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


# ===== @register_plugin 装饰器 =====

def register_plugin(cls: Type[Plugin]) -> Type[Plugin]:
    """插件注册装饰器。

    用法：
        @register_plugin
        class MyPlugin(Plugin):
            name = "my_plugin"
            version = "0.1.0"

            async def on_load(self):
                ...
    """
    get_plugin_registry().register(cls)
    return cls