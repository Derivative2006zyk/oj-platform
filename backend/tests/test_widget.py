import pytest


async def _register_and_login(client, username: str = "alice") -> str:
    await client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "secret123",
        },
    )
    res = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "secret123"},
    )
    return res.json()["access_token"]


async def _create_problem(client, title: str = "test") -> int:
    res = await client.post(
        "/api/admin/problems",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={
            "title": title,
            "category_id": 1,
            "description": "test",
            "type": "algorithm",
            "difficulty": 1,
        },
    )
    return res.json()["id"]


@pytest.mark.asyncio
async def test_widget_summary_requires_auth(client):
    res = await client.get("/api/widget/summary")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_widget_summary_empty(client):
    token = await _register_and_login(client)

    res = await client.get(
        "/api/widget/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    data = res.json()
    assert data["total_submissions"] == 0
    assert data["today_submissions"] == 0
    assert data["total_accepted"] == 0
    assert data["acceptance_rate"] == 0.0
    assert data["solved_problems"] == 0
    assert data["total_problems"] >= 0
    assert data["latest_submission"] is None


@pytest.mark.asyncio
async def test_widget_summary_with_submissions(client):
    token = await _register_and_login(client)
    pid = await _create_problem(client)

    # 3 次提交
    for i in range(3):
        await client.post(
            "/api/submissions",
            headers={"Authorization": f"Bearer {token}"},
            json={"problem_id": pid, "code": f"print({i})", "language": "python"},
        )

    res = await client.get(
        "/api/widget/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    data = res.json()
    assert data["total_submissions"] == 3
    assert data["today_submissions"] == 3
    assert data["latest_submission"] is not None
    assert data["latest_submission"]["problem_id"] == pid
    assert data["latest_submission"]["language"] == "python"


@pytest.mark.asyncio
async def test_widget_summary_only_current_user(client):
    """只能看到自己的统计。"""
    token_a = await _register_and_login(client, "alice")
    token_b = await _register_and_login(client, "bob")
    pid = await _create_problem(client)

    # alice 提交 2 次
    for i in range(2):
        await client.post(
            "/api/submissions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"problem_id": pid, "code": f"print({i})", "language": "python"},
        )

    # alice 看到 2
    res = await client.get(
        "/api/widget/summary",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res.json()["total_submissions"] == 2

    # bob 看到 0
    res = await client.get(
        "/api/widget/summary",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.json()["total_submissions"] == 0