import pytest

from app.core import plugin_registry as registry_module
from app.core.plugin_base import Plugin
from app.core.plugin_registry import PluginRegistry


@pytest.fixture(autouse=True)
def clean_global_classes():
    """每个用例前后清空全局插件类列表，避免用例互相污染。"""
    registry_module._plugin_classes.clear()
    yield
    registry_module._plugin_classes.clear()


def make_registry(*classes) -> PluginRegistry:
    """按当前架构：类通过全局列表收集，再由 _build_instances 实例化。"""
    for cls in classes:
        registry_module._plugin_classes.append(cls)
    reg = PluginRegistry()
    reg._build_instances()
    return reg


class DummyPlugin(Plugin):
    name = "dummy"
    version = "0.1.0"
    dependencies = []

    def __init__(self):
        self.loaded = False
        self.enabled = False
        self.disabled = False
        self.unloaded = False

    async def on_load(self):
        self.loaded = True

    async def on_enable(self):
        self.enabled = True

    async def on_disable(self):
        self.disabled = True

    async def on_unload(self):
        self.unloaded = True


class RoutedPlugin(Plugin):
    name = "routed"
    version = "0.1.0"
    dependencies = []

    async def on_load(self):
        pass

    def get_routers(self):
        from fastapi import APIRouter
        router = APIRouter(prefix="/dummy-route", tags=["dummy"])

        @router.get("/ping")
        async def ping():
            return {"pong": True}

        return [router]


def test_build_instances_and_list():
    reg = make_registry(DummyPlugin)
    plugins = reg.list_plugins()

    assert len(plugins) == 1
    assert plugins[0]["name"] == "dummy"
    assert plugins[0]["version"] == "0.1.0"
    assert reg.get("dummy") is not None


def test_collect_routers():
    reg = make_registry(RoutedPlugin)
    routers = reg.collect_routers()

    assert len(routers) == 1


def test_collect_routers_skips_disabled():
    reg = make_registry(RoutedPlugin)
    reg.get("routed")._enabled = False

    assert reg.collect_routers() == []


@pytest.mark.asyncio
async def test_load_all_calls_on_load():
    reg = make_registry(DummyPlugin)
    await reg.load_all()

    assert reg.get("dummy").loaded is True

    await reg.unload_all()
    assert reg.get("dummy").unloaded is True


@pytest.mark.asyncio
async def test_enable_disable_single():
    reg = make_registry(DummyPlugin)
    await reg.load_all()

    await reg.enable("dummy")
    assert reg.get("dummy").enabled is True

    await reg.disable("dummy")
    assert reg.get("dummy").disabled is True


def test_discover_external_skips_incomplete_dirs(tmp_path):
    """缺少 manifest.json 或 backend/__init__.py 的目录应被忽略。"""
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "manifest.json").write_text("{}", encoding="utf-8")

    reg = PluginRegistry()
    reg.discover_external(str(tmp_path))  # 不应抛异常

    assert reg.list_plugins() == []


def test_register_plugin_decorator_rejects_non_plugin():
    def not_a_plugin():
        pass

    with pytest.raises(TypeError):
        registry_module.register_plugin(not_a_plugin)


@pytest.mark.asyncio
async def test_health_returns_status_ok(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"