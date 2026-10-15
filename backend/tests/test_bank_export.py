import io
import json
import zipfile

import pytest


async def _create_problem(client, title: str = "导出测试题", type_: str = "algorithm") -> int:
    body = {
        "title": title,
        "category_id": 1,
        "description": "示例描述",
        "type": type_,
        "difficulty": 1,
        "answer": "答案",
        "explanation": "解析",
    }
    if type_ == "algorithm":
        body["test_cases"] = [
            {"input_data": "1 2", "expected_output": "3", "is_example": True}
        ]
    res = await client.post(
        "/api/admin/problems",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json=body,
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


@pytest.mark.asyncio
async def test_export_requires_admin_key(client):
    res = await client.post(
        "/api/admin/bank/export",
        json={"problem_ids": None},
    )
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_export_all(client):
    await _create_problem(client, "导出 A")
    await _create_problem(client, "导出 B")

    res = await client.post(
        "/api/admin/bank/export",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={"problem_ids": None},
    )
    assert res.status_code == 200
    assert "zip" in res.headers["content-type"]

    zf = zipfile.ZipFile(io.BytesIO(res.content))
    names = zf.namelist()
    assert "manifest.json" in names

    manifest = json.loads(zf.read("manifest.json"))
    assert manifest["format"] == "oj-platform-bank"
    assert manifest["format_version"] == 1
    assert manifest["problem_count"] >= 2

    titles = [p["title"] for p in manifest["problems"]]
    assert "导出 A" in titles
    assert "导出 B" in titles


@pytest.mark.asyncio
async def test_export_selected(client):
    pid_a = await _create_problem(client, "选中 A")
    await _create_problem(client, "未选中 B")

    res = await client.post(
        "/api/admin/bank/export",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={"problem_ids": [pid_a]},
    )
    assert res.status_code == 200

    zf = zipfile.ZipFile(io.BytesIO(res.content))
    manifest = json.loads(zf.read("manifest.json"))
    titles = [p["title"] for p in manifest["problems"]]
    assert "选中 A" in titles
    assert "未选中 B" not in titles


@pytest.mark.asyncio
async def test_export_empty(client):
    res = await client.post(
        "/api/admin/bank/export",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={"problem_ids": [999999]},
    )
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_export_by_bank(client):
    bres = await client.post(
        "/api/admin/banks",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={"name": "导出专用题库", "sort_order": 1},
    )
    assert bres.status_code == 201
    bid = bres.json()["id"]

    for i in range(2):
        await client.post(
            "/api/admin/problems",
            headers={"X-Admin-Key": "admin-key-change-me"},
            json={
                "title": f"题库内 {i}",
                "category_id": 1,
                "bank_id": bid,
                "description": "x",
                "type": "algorithm",
                "difficulty": 1,
            },
        )
    await client.post(
        "/api/admin/problems",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={
            "title": "题库外",
            "category_id": 1,
            "description": "x",
            "type": "algorithm",
            "difficulty": 1,
        },
    )

    res = await client.post(
        "/api/admin/bank/export",
        headers={"X-Admin-Key": "admin-key-change-me"},
        json={"bank_id": bid},
    )
    assert res.status_code == 200

    zf = zipfile.ZipFile(io.BytesIO(res.content))
    manifest = json.loads(zf.read("manifest.json"))
    titles = [p["title"] for p in manifest["problems"]]
    assert "题库内 0" in titles
    assert "题库内 1" in titles
    assert "题库外" not in titles
    assert any(p.get("bank_name") == "导出专用题库" for p in manifest["problems"])