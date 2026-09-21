# backend/tests/conftest.py
import asyncio
import os

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = (
    os.environ.get("TEST_DATABASE_URL")
    or "postgresql+asyncpg://oj:oj_password@localhost:5432/oj_platform_test"
)
os.environ["REDIS_URL"] = (
    os.environ.get("TEST_REDIS_URL")
    or "redis://localhost:6379/1"
)
os.environ["EVENT_BUS_CHANNEL"] = (
    os.environ.get("TEST_EVENT_BUS_CHANNEL")
    or "oj:events:test"
)

import app.models  # noqa: F401

import pytest
from httpx import AsyncClient, ASGITransport
from redis.asyncio import Redis

from app.main import app
from app.database import Base, engine, async_session
from app.models.category import Category
from app.core.event_bus import get_event_bus


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        session.add_all([
            Category(name="算法", sort_order=1),
            Category(name="数学", sort_order=2),
            Category(name="物理", sort_order=3),
            Category(name="英语", sort_order=4),
            Category(name="其他", sort_order=99),
        ])
        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def flush_redis():
    r = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    await r.flushdb()
    yield
    await r.flushdb()
    await r.aclose()


@pytest.fixture(autouse=True)
def reset_event_bus_between_tests():
    import app.core.event_bus as eb_module
    eb_module._event_bus = None
    yield
    eb_module._event_bus = None


@pytest.fixture
async def client():
    bus = get_event_bus()
    await bus.connect()
    await bus.start_listening()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    await bus.disconnect()
    bus.clear_handlers()