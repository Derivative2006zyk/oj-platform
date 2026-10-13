import pytest


async def _register_and_login(client, username: str = "blank_user") -> str:
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


async def _create_blank_problem(client, blanks: list) -> int:
    res = await client.post(
        "/api/admin/problems",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={
            "title": "填空题测试",
            "category_id": 1,
            "description": "填空：1+1=__，2+2=__",
            "type": "fill_blank",
            "difficulty": 1,
            "blanks": blanks,
        },
    )
    assert res.status_code in (200, 201), res.text
    return res.json()["id"]


async def _submit(client, token: str, pid: int, blanks: list):
    return await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "language": "fill_blank",
            "answer_data": {"blanks": blanks},
        },
    )


@pytest.mark.asyncio
async def test_fill_blank_all_correct(client):
    token = await _register_and_login(client, "fb_ac")
    pid = await _create_blank_problem(client, [
        {"blank_index": 1, "correct_answers": ["2"], "match_rule": "exact"},
        {"blank_index": 2, "correct_answers": ["4"], "match_rule": "exact"},
    ])

    res = await _submit(client, token, pid, ["2", "4"])
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["submission_kind"] == "fill_blank"
    assert data["status"] == "AC"
    assert data["passed_cases"] == 2
    assert data["total_cases"] == 2


@pytest.mark.asyncio
async def test_fill_blank_partial(client):
    token = await _register_and_login(client, "fb_partial")
    pid = await _create_blank_problem(client, [
        {"blank_index": 1, "correct_answers": ["2"], "match_rule": "exact"},
        {"blank_index": 2, "correct_answers": ["4"], "match_rule": "exact"},
    ])

    res = await _submit(client, token, pid, ["2", "5"])
    data = res.json()
    assert data["status"] == "WA"
    assert data["passed_cases"] == 1
    assert data["total_cases"] == 2


@pytest.mark.asyncio
async def test_fill_blank_all_wrong(client):
    token = await _register_and_login(client, "fb_wa")
    pid = await _create_blank_problem(client, [
        {"blank_index": 1, "correct_answers": ["2"], "match_rule": "exact"},
    ])

    res = await _submit(client, token, pid, ["99"])
    data = res.json()
    assert data["status"] == "WA"
    assert data["passed_cases"] == 0


@pytest.mark.asyncio
async def test_fill_blank_multiple_answers(client):
    """一个空可以有多个正确写法。"""
    token = await _register_and_login(client, "fb_multi")
    pid = await _create_blank_problem(client, [
        {"blank_index": 1, "correct_answers": ["3", "三"], "match_rule": "exact"},
    ])

    res = await _submit(client, token, pid, ["三"])
    data = res.json()
    assert data["status"] == "AC"


@pytest.mark.asyncio
async def test_fill_blank_ignore_case(client):
    token = await _register_and_login(client, "fb_case")
    pid = await _create_blank_problem(client, [
        {"blank_index": 1, "correct_answers": ["Hello"], "match_rule": "ignore_case"},
    ])

    res = await _submit(client, token, pid, ["hello"])
    data = res.json()
    assert data["status"] == "AC"


@pytest.mark.asyncio
async def test_fill_blank_exact_case_sensitive(client):
    token = await _register_and_login(client, "fb_exact_case")
    pid = await _create_blank_problem(client, [
        {"blank_index": 1, "correct_answers": ["Hello"], "match_rule": "exact"},
    ])

    res = await _submit(client, token, pid, ["hello"])
    data = res.json()
    assert data["status"] == "WA"


@pytest.mark.asyncio
async def test_fill_blank_empty_answer(client):
    token = await _register_and_login(client, "fb_empty")
    pid = await _create_blank_problem(client, [
        {"blank_index": 1, "correct_answers": ["2"], "match_rule": "exact"},
    ])

    res = await _submit(client, token, pid, [""])
    data = res.json()
    assert data["status"] == "WA"


@pytest.mark.asyncio
async def test_fill_blank_missing_answer_data(client):
    token = await _register_and_login(client, "fb_422")
    pid = await _create_blank_problem(client, [
        {"blank_index": 1, "correct_answers": ["2"], "match_rule": "exact"},
    ])

    res = await client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_id": pid,
            "language": "fill_blank",
        },
    )
    assert res.status_code == 422