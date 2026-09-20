import pytest

from app.core.plugin_config_store import (
    ensure_config,
    get_config,
    get_all_configs,
    set_enabled,
    update_config,
)


@pytest.mark.asyncio
async def test_ensure_config_creates_new():
    config = await ensure_config("test_plugin_a")
    assert config.plugin_name == "test_plugin_a"
    assert config.enabled is True
    assert config.config == {}


@pytest.mark.asyncio
async def test_ensure_config_does_not_duplicate():
    a = await ensure_config("test_plugin_b")
    b = await ensure_config("test_plugin_b")
    assert a.id == b.id


@pytest.mark.asyncio
async def test_set_enabled_toggles():
    await ensure_config("test_plugin_c", default_enabled=True)

    config = await set_enabled("test_plugin_c", False)
    assert config.enabled is False

    config = await set_enabled("test_plugin_c", True)
    assert config.enabled is True


@pytest.mark.asyncio
async def test_get_all_configs():
    await ensure_config("test_plugin_d")
    await ensure_config("test_plugin_e")

    configs = await get_all_configs()
    assert "test_plugin_d" in configs
    assert "test_plugin_e" in configs


@pytest.mark.asyncio
async def test_update_config():
    await ensure_config("test_plugin_f")

    updated = await update_config("test_plugin_f", {"api_key": "xxx"})
    assert updated.config == {"api_key": "xxx"}


@pytest.mark.asyncio
async def test_get_config_returns_none_for_missing():
    config = await get_config("nonexistent_plugin")
    assert config is None