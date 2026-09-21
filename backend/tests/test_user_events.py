# backend/tests/test_user_events.py

import asyncio

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.event_bus import get_event_bus
from app.core.events import EventNames


@pytest.mark.asyncio
async def test_user_events_publish(setup_database):
    bus = get_event_bus()
    await bus.connect()

    registered = []
    logged_in = []

    async def on_registered(payload):
        registered.append(payload)

    async def on_logged_in(payload):
        logged_in.append(payload)

    bus.subscribe(EventNames.USER_REGISTERED, on_registered)
    bus.subscribe(EventNames.USER_LOGGED_IN, on_logged_in)
    await bus.start_listening()

    print(f"\n[debug] handlers: {list(bus._handlers.keys())}")
    print(f"[debug] pubsub channels: {bus._pubsub.channels}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        res = await c.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "secret123"},
        )
        assert res.status_code == 201

        for _ in range(100):
            if registered:
                break
            await asyncio.sleep(0.02)
        print(f"[debug] after register: registered={registered}, logged_in={logged_in}")
        assert len(registered) >= 1

        res = await c.post(
            "/api/auth/login",
            json={"username": "alice", "password": "secret123"},
        )
        assert res.status_code == 200

        print(f"[debug] after login request: pubsub channels={bus._pubsub.channels}")
        print(f"[debug] logged_in={logged_in}")

        for _ in range(100):
            if logged_in:
                break
            await asyncio.sleep(0.02)

        print(f"[debug] final: logged_in={logged_in}")
        assert len(logged_in) >= 1

    await bus.disconnect()
    bus.clear_handlers()


@pytest.mark.asyncio
async def test_login_failure_does_not_publish(setup_database):
    bus = get_event_bus()
    await bus.connect()

    received = []

    async def handler(payload):
        received.append(payload)

    bus.subscribe(EventNames.USER_LOGGED_IN, handler)
    await bus.start_listening()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        res = await c.post(
            "/api/auth/login",
            json={"username": "nobody", "password": "wrong"},
        )
        assert res.status_code == 401

    await asyncio.sleep(0.3)
    assert received == []

    await bus.disconnect()
    bus.clear_handlers()