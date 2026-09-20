import asyncio

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.event_bus import get_event_bus
from app.core.events import EventNames


@pytest.mark.asyncio
async def test_create_problem_publishes_event(setup_database):
    """创建题目后应发布 problem.created 事件。"""
    bus = get_event_bus()
    await bus.connect()

    received = []

    async def handler(payload: dict):
        received.append(payload)

    bus.subscribe(EventNames.PROBLEM_CREATED, handler)
    await bus.start_listening()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        res = await c.post(
            "/api/admin/problems",
            headers={"X-Admin-Key": "admin-key-change-me"},
            json={
                "title": "事件测试题",
                "category_id": 1,
                "description": "test",
                "type": "algorithm",
                "difficulty": 1,
            },
        )
        assert res.status_code == 201

    for _ in range(50):
        if received:
            break
        await asyncio.sleep(0.02)

    assert len(received) >= 1
    assert received[0]["title"] == "事件测试题"

    await bus.disconnect()
    bus.clear_handlers()


@pytest.mark.asyncio
async def test_update_problem_publishes_event(setup_database):
    """更新题目后应发布 problem.updated 事件。"""
    bus = get_event_bus()
    await bus.connect()

    received = []

    async def handler(payload: dict):
        received.append(payload)

    bus.subscribe(EventNames.PROBLEM_UPDATED, handler)
    await bus.start_listening()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # 先创建
        res = await c.post(
            "/api/admin/problems",
            headers={"X-Admin-Key": "admin-key-change-me"},
            json={
                "title": "待更新题",
                "category_id": 1,
                "description": "test",
                "type": "algorithm",
                "difficulty": 1,
            },
        )
        assert res.status_code == 201
        problem_id = res.json()["id"]

        # 再更新
        res = await c.put(
            f"/api/admin/problems/{problem_id}",
            headers={"X-Admin-Key": "admin-key-change-me"},
            json={"title": "已更新题"},
        )
        assert res.status_code == 200

    for _ in range(50):
        if received:
            break
        await asyncio.sleep(0.02)

    assert len(received) >= 1
    assert received[0]["title"] == "已更新题"

    await bus.disconnect()
    bus.clear_handlers()


@pytest.mark.asyncio
async def test_delete_problem_publishes_event(setup_database):
    """删除题目后应发布 problem.deleted 事件。"""
    bus = get_event_bus()
    await bus.connect()

    received = []

    async def handler(payload: dict):
        received.append(payload)

    bus.subscribe(EventNames.PROBLEM_DELETED, handler)
    await bus.start_listening()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # 先创建
        res = await c.post(
            "/api/admin/problems",
            headers={"X-Admin-Key": "admin-key-change-me"},
            json={
                "title": "待删除题",
                "category_id": 1,
                "description": "test",
                "type": "algorithm",
                "difficulty": 1,
            },
        )
        assert res.status_code == 201
        problem_id = res.json()["id"]

        # 再删除
        res = await c.delete(
            f"/api/admin/problems/{problem_id}",
            headers={"X-Admin-Key": "admin-key-change-me"},
        )
        assert res.status_code == 200

    for _ in range(50):
        if received:
            break
        await asyncio.sleep(0.02)

    assert len(received) >= 1
    assert received[0]["id"] == problem_id

    await bus.disconnect()
    bus.clear_handlers()