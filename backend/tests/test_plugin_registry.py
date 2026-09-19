import pytest

from app.core.plugin_base import Plugin
from app.core.plugin_registry import PluginRegistry


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


class DependentPlugin(Plugin):
    name = "dependent"
    version = "0.1.0"
    dependencies = ["dummy"]

    async def on_load(self):
        pass


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


def test_register_and_list():
    reg = PluginRegistry()
    reg.register(DummyPlugin)

    reg._build_instances()
    plugins = reg.list_plugins()

    assert len(plugins) == 1
    assert plugins[0]["name"] == "dummy"
    assert plugins[0]["version"] == "0.1.0"


def test_duplicate_name_rejected():
    reg = PluginRegistry()
    reg.register(DummyPlugin)

    class AnotherDummy(Plugin):
        name = "dummy"
        version = "0.2.0"

        async def on_load(self):
            pass

    with pytest.raises(ValueError, match="name conflict"):
        reg.register(AnotherDummy)


def test_missing_name_rejected():
    reg = PluginRegistry()

    class NamelessPlugin(Plugin):
        version = "0.1.0"

        async def on_load(self):
            pass

    with pytest.raises(ValueError, match="non-empty 'name'"):
        reg.register(NamelessPlugin)


@pytest.mark.asyncio
async def test_load_all_calls_lifecycle():
    reg = PluginRegistry()
    reg.register(DummyPlugin)

    await reg.load_all()

    plugin = reg.get("dummy")
    assert plugin.loaded is True
    assert plugin.enabled is True

    await reg.unload_all()
    assert plugin.disabled is True
    assert plugin.unloaded is True


@pytest.mark.asyncio
async def test_topological_order():
    reg = PluginRegistry()
    reg.register(DependentPlugin)
    reg.register(DummyPlugin)

    await reg.load_all()

    # 不报错说明拓扑排序正确
    assert reg.get("dependent") is not None
    assert reg.get("dummy") is not None

    await reg.unload_all()


def test_circular_dependency_detected():
    reg = PluginRegistry()

    class A(Plugin):
        name = "a"
        version = "0.1.0"
        dependencies = ["b"]

        async def on_load(self):
            pass

    class B(Plugin):
        name = "b"
        version = "0.1.0"
        dependencies = ["a"]

        async def on_load(self):
            pass

    reg.register(A)
    reg.register(B)
    reg._build_instances()

    with pytest.raises(ValueError, match="Circular dependency"):
        reg._topological_order()


def test_collect_routers():
    reg = PluginRegistry()
    reg.register(RoutedPlugin)

    reg._build_instances()
    routers = reg.collect_routers()

    assert len(routers) == 1


@pytest.mark.asyncio
async def test_enable_disable_single():
    reg = PluginRegistry()
    reg.register(DummyPlugin)
    reg._build_instances()

    await reg.enable("dummy")
    assert reg.get("dummy").enabled is True

    await reg.disable("dummy")
    assert reg.get("dummy").disabled is True


@pytest.mark.asyncio
async def test_health_with_plugins(client):
    """验证改造后 /health 仍返回正常。"""
    res = await client.get("/health")
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "ok"
    assert data["redis"] == "ok"