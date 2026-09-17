# backend/tests/test_event_bus.py
import asyncio

import pytest

from app.core.config import settings
from app.core.event_bus import EventBus


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus(settings.REDIS_URL)
    await bus.connect()

    received = []

    async def handler(payload: dict):
        received.append(payload)

    bus.subscribe("test.event.publish", handler)
    await bus.start_listening()

    await bus.publish("test.event.publish", {"problem_id": 1})

    for _ in range(50):
        if received:
            break
        await asyncio.sleep(0.02)

    assert received == [{"problem_id": 1}]
    await bus.disconnect()


@pytest.mark.asyncio
async def test_event_bus_multiple_handlers():
    bus = EventBus(settings.REDIS_URL)
    await bus.connect()

    received_a = []
    received_b = []

    async def handler_a(payload: dict):
        received_a.append(payload)

    async def handler_b(payload: dict):
        received_b.append(payload)

    bus.subscribe("test.event.multi", handler_a)
    bus.subscribe("test.event.multi", handler_b)
    await bus.start_listening()

    await bus.publish("test.event.multi", {"problem_id": 2})

    for _ in range(50):
        if received_a and received_b:
            break
        await asyncio.sleep(0.02)

    assert received_a == [{"problem_id": 2}]
    assert received_b == [{"problem_id": 2}]
    await bus.disconnect()


@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    bus = EventBus(settings.REDIS_URL)
    await bus.connect()

    received = []

    async def handler(payload: dict):
        received.append(payload)

    bus.subscribe("test.event.unsub", handler)
    bus.unsubscribe("test.event.unsub", handler)
    await bus.start_listening()

    await bus.publish("test.event.unsub", {"problem_id": 3})
    await asyncio.sleep(0.2)

    assert received == []
    await bus.disconnect()


@pytest.mark.asyncio
async def test_event_bus_clear_handlers():
    bus = EventBus(settings.REDIS_URL)
    await bus.connect()

    async def handler(payload: dict):
        pass

    bus.subscribe("test.event.clear", handler)
    assert bus.list_subscribed_channels() == ["test.event.clear"]

    bus.clear_handlers()
    assert bus.list_subscribed_channels() == []

    await bus.disconnect()


@pytest.mark.asyncio
async def test_health_redis(client):
    res = await client.get("/health")
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "ok"
    assert data["redis"] == "ok"