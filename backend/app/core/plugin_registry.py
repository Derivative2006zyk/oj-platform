import asyncio
import importlib
import importlib.util
import json
import pkgutil
import sys
from pathlib import Path
from typing import Dict, List, Type

from fastapi import APIRouter

from app.core.plugin_base import Plugin

# 全局变量，用于收集被 @register_plugin 装饰的类
_plugin_classes: List[Type[Plugin]] = []
_registry_instance = None

PLUGINS_INSTALLED_DIR = Path("/app/plugins_installed")


def register_plugin(cls: Type[Plugin]) -> Type[Plugin]:
    """装饰器：标记一个类为插件，并将其加入全局列表"""
    if not issubclass(cls, Plugin):
        raise TypeError(f"{cls} is not a subclass of Plugin")
    if cls not in _plugin_classes:
        _plugin_classes.append(cls)
    return cls


class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}

    # ===== 发现与加载 =====

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
            if not item.is_dir():
                continue
            manifest_file = item / "manifest.json"
            entry_file = item / "backend" / "__init__.py"
            if not (manifest_file.exists() and entry_file.exists()):
                continue

            plugin_name = item.name
            mod_name = f"ext_plugin_{plugin_name}"

            # 如果已经加载过，跳过（避免重复注册）
            if mod_name in sys.modules:
                continue

            print(f"[PluginRegistry] Found external plugin: {plugin_name}")
            try:
                spec = importlib.util.spec_from_file_location(mod_name, entry_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
            except Exception as e:
                print(f"[PluginRegistry] Failed to load external plugin {plugin_name}: {e}")

    def reload_external(self, plugin_dir: str) -> None:
        """重新扫描外部插件（安装后立即调用），将新插件类注册进来并实例化"""
        self.discover_external(plugin_dir)
        self._build_instances()

    def _build_instances(self) -> None:
        """将全局列表中收集到的类实例化，存入 _plugins 字典（已存在则跳过）"""
        for cls in _plugin_classes:
            try:
                instance = cls()
                if instance.name not in self._plugins:
                    self._plugins[instance.name] = instance
            except Exception as e:
                print(f"[PluginRegistry] Error instantiating {cls.__name__}: {e}")

    async def load_all(self) -> None:
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

    # ===== 启用/禁用 =====

    async def enable(self, name: str) -> None:
        if name in self._plugins:
            await self._plugins[name].on_enable()

    async def disable(self, name: str) -> None:
        if name in self._plugins:
            await self._plugins[name].on_disable()

    # ===== 安装/卸载（Day 52 新增） =====

    async def install_plugin(self, name: str) -> None:
        """插件文件已落盘后调用：重新扫描 → 实例化 → 触发 on_install"""
        self.reload_external(str(PLUGINS_INSTALLED_DIR))

        plugin = self._plugins.get(name)
        if plugin is None:
            raise RuntimeError(f"Plugin class for '{name}' not found after reload")

        plugin_dir = PLUGINS_INSTALLED_DIR / name
        print(f"[PluginRegistry] invoking on_install for {name} at {plugin_dir}")
        await plugin.on_install(plugin_dir)
        print(f"[PluginRegistry] on_install finished for {name}")

    async def uninstall_plugin(self, name: str) -> None:
        """触发 on_uninstall 并从内存中移除（路由会在下次重启后消失）"""
        plugin = self._plugins.get(name)
        plugin_dir = PLUGINS_INSTALLED_DIR / name

        if plugin is not None:
            try:
                print(f"[PluginRegistry] invoking on_uninstall for {name}")
                await plugin.on_uninstall(plugin_dir)
            except Exception as e:
                print(f"[PluginRegistry] on_uninstall error {name}: {e}")
            finally:
                try:
                    await plugin.on_unload()
                except Exception:
                    pass
                self._plugins.pop(name, None)

        # 即便没有实例，也尝试兜底清理可能的容器
        compose_file = plugin_dir / "docker-compose.yml"
        if compose_file.exists():
            await _run_compose_down(name, compose_file)

    # ===== 查询 =====

    def get(self, name: str) -> Plugin | None:
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

    def get_ui_manifests(self) -> List[dict]:
        results = []
        path = PLUGINS_INSTALLED_DIR
        if not path.exists():
            return results
        for item in path.iterdir():
            if item.is_dir():
                manifest_file = item / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            data["folder_name"] = item.name
                            results.append(data)
                    except Exception as e:
                        print(f"[PluginRegistry] Error reading manifest {item.name}: {e}")
        return results


# ===== Docker Compose 辅助函数 =====

async def _run_compose_down(plugin_name: str, compose_file: Path) -> None:
    """兜底：直接执行 docker compose down"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose",
            "-p", f"oj-plugin-{plugin_name}",
            "-f", str(compose_file),
            "down",
            "--remove-orphans",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"[PluginRegistry] compose down failed: {stderr.decode()[:500]}")
    except Exception as e:
        print(f"[PluginRegistry] compose down exception: {e}")


def get_plugin_registry() -> PluginRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PluginRegistry()
    return _registry_instance