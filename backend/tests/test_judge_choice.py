import pytest


async def _register_and_login(client, username: str = "choice_user") -> str:
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


async def _create_choice_problem(client, options: list) -> int:
    res = await client.post(
        "/api/admin/problems",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={
            "title": "选择题测试",
            "category_id": 1,
            "description": "以下哪个是排序算法？",
            "type": "choice",
            "difficulty": 1,
            "options": options,
        },
    )
    assert res.status_code in (200, 201), res.text
    return res.json()["id"]


@pytest.mark.asyncio
async def test_choice_correct(client):
    token = await _register_and_login(client, "choice_ac")
    pid = await _create_choice_problem(client, [
        {"key": "A", "content": "冒泡排序", "is_correct": True},
        {"key": "B", "content": "二分查找", "is_correct": False},
        {"key": "C", "content": "哈希", "is_correct": False},
    ])

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "language": "choice",
            "answer_data": {"selected": "A"},
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["submission_kind"] == "choice"
    assert data["status"] == "AC"
    assert data["passed_cases"] == 1
    assert data["total_cases"] == 1


@pytest.mark.asyncio
async def test_choice_wrong(client):
    token = await _register_and_login(client, "choice_wa")
    pid = await _create_choice_problem(client, [
        {"key": "A", "content": "冒泡排序", "is_correct": True},
        {"key": "B", "content": "二分查找", "is_correct": False},
    ])

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "language": "choice",
            "answer_data": {"selected": "B"},
        },
    )
    data = res.json()
    assert data["status"] == "WA"
    assert data["passed_cases"] == 0


@pytest.mark.asyncio
async def test_choice_empty_selection(client):
    token = await _register_and_login(client, "choice_empty")
    pid = await _create_choice_problem(client, [
        {"key": "A", "content": "x", "is_correct": True},
    ])

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "language": "choice",
            "answer_data": {"selected": ""},
        },
    )
    data = res.json()
    assert data["status"] == "WA"


@pytest.mark.asyncio
async def test_choice_multi_correct(client):
    token = await _register_and_login(client, "choice_multi")
    pid = await _create_choice_problem(client, [
        {"key": "A", "content": "x", "is_correct": True},
        {"key": "B", "content": "y", "is_correct": True},
        {"key": "C", "content": "z", "is_correct": False},
    ])

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "language": "choice",
            "answer_data": {"selected": ["A", "B"]},
        },
    )
    data = res.json()
    assert data["status"] == "AC"


@pytest.mark.asyncio
async def test_choice_multi_partial(client):
    token = await _register_and_login(client, "choice_multi_p")
    pid = await _create_choice_problem(client, [
        {"key": "A", "content": "x", "is_correct": True},
        {"key": "B", "content": "y", "is_correct": True},
    ])

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "language": "choice",
            "answer_data": {"selected": ["A"]},
        },
    )
    data = res.json()
    assert data["status"] == "WA"


@pytest.mark.asyncio
async def test_choice_requires_answer_data(client):
    token = await _register_and_login(client, "choice_422")
    pid = await _create_choice_problem(client, [
        {"key": "A", "content": "x", "is_correct": True},
    ])

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "language": "choice",
        },
    )
    assert res.status_code == 422