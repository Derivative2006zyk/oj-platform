import pytest


async def _create_bank(client, name: str = "测试题库", sort_order: int = 0) -> int:
    res = await client.post(
        "/api/admin/banks",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={"name": name, "description": "desc", "sort_order": sort_order},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def _create_problem(client, title: str, bank_id=None) -> int:
    body = {
        "title": title,
        "category_id": 1,
        "description": "描述",
        "type": "algorithm",
        "difficulty": 1,
    }
    if bank_id is not None:
        body["bank_id"] = bank_id
    res = await client.post(
        "/api/admin/problems",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json=body,
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


@pytest.mark.asyncio
async def test_create_and_list_banks(client):
    bid = await _create_bank(client, "题库 A")
    res = await client.get("/api/banks")
    assert res.status_code == 200
    banks = res.json()
    assert any(b["id"] == bid and b["name"] == "题库 A" for b in banks)


@pytest.mark.asyncio
async def test_bank_problem_count(client):
    bid = await _create_bank(client, "题库计数")
    await _create_problem(client, "题 1", bank_id=bid)
    await _create_problem(client, "题 2", bank_id=bid)

    res = await client.get("/api/banks")
    banks = res.json()
    target = next(b for b in banks if b["id"] == bid)
    assert target["problem_count"] == 2


@pytest.mark.asyncio
async def test_filter_by_bank(client):
    bid_a = await _create_bank(client, "题库 A2")
    bid_b = await _create_bank(client, "题库 B2")
    await _create_problem(client, "A-1", bank_id=bid_a)
    await _create_problem(client, "A-2", bank_id=bid_a)
    await _create_problem(client, "B-1", bank_id=bid_b)
    await _create_problem(client, "无题库")

    res = await client.get(f"/api/problems?bank_id={bid_a}&page_size=50")
    items = res.json()["items"]
    titles = [p["title"] for p in items]
    assert "A-1" in titles
    assert "A-2" in titles
    assert "B-1" not in titles


@pytest.mark.asyncio
async def test_filter_unassigned(client):
    bid = await _create_bank(client, "某题库")
    await _create_problem(client, "有归属", bank_id=bid)
    await _create_problem(client, "无归属")

    res = await client.get("/api/problems?unassigned=true&page_size=50")
    items = res.json()["items"]
    titles = [p["title"] for p in items]
    assert "无归属" in titles
    assert "有归属" not in titles


@pytest.mark.asyncio
async def test_delete_bank_sets_null(client):
    bid = await _create_bank(client, "待删题库")
    pid = await _create_problem(client, "被清归属", bank_id=bid)

    res = await client.delete(
        f"/api/admin/banks/{bid}",
        headers={"X-Admin-Key": "admin-key-change-me"},
    )
    assert res.status_code == 200

    detail = await client.get(f"/api/problems/{pid}")
    assert detail.status_code == 200
    assert detail.json()["bank_id"] is None


@pytest.mark.asyncio
async def test_update_bank(client):
    bid = await _create_bank(client, "旧名")
    res = await client.put(
        f"/api/admin/banks/{bid}",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={"name": "新名", "sort_order": 5},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "新名"
    assert data["sort_order"] == 5