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


async def _create_problem(client, title: str = "两数之和") -> int:
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
async def test_submit_requires_auth(client):
    res = await client.post(
        "/api/submissions",
        json={"problem_id": 1, "code": "print(1)", "language": "python"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_submit_success(client):
    token = await _register_and_login(client)
    pid = await _create_problem(client)

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "code": "print('hello')",
            "language": "python",
        },
    )
    assert res.status_code == 201

    data = res.json()
    assert data["problem_id"] == pid
    assert data["language"] == "python"
    assert data["status"] == "PENDING"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_my_submissions(client):
    token = await _register_and_login(client)
    pid = await _create_problem(client)

    for i in range(3):
        await client.post(
            "/api/submissions",
            headers={"Authorization": f"Bearer {token}"},
            json={"problem_id": pid, "code": f"print({i})", "language": "python"},
        )

    res = await client.get(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_get_submission_detail(client):
    token = await _register_and_login(client)
    pid = await _create_problem(client)

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={"problem_id": pid, "code": "print(42)", "language": "python"},
    )
    sid = res.json()["id"]

    res = await client.get(
        f"/api/submissions/{sid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["code"] == "print(42)"


@pytest.mark.asyncio
async def test_cannot_get_others_submission(client):
    token_a = await _register_and_login(client, "alice")
    token_b = await _register_and_login(client, "bob")
    pid = await _create_problem(client)

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"problem_id": pid, "code": "print(1)", "language": "python"},
    )
    sid = res.json()["id"]

    # bob 尝试访问 alice 的提交
    res = await client.get(
        f"/api/submissions/{sid}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_problem_submissions(client):
    token = await _register_and_login(client)
    pid = await _create_problem(client)

    for i in range(2):
        await client.post(
            "/api/submissions",
            headers={"Authorization": f"Bearer {token}"},
            json={"problem_id": pid, "code": f"print({i})", "language": "python"},
        )

    res = await client.get(
        f"/api/problems/{pid}/submissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["total"] == 2


@pytest.mark.asyncio
async def test_submit_empty_code_rejected(client):
    token = await _register_and_login(client)
    pid = await _create_problem(client)

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={"problem_id": pid, "code": "", "language": "python"},
    )
    assert res.status_code == 422