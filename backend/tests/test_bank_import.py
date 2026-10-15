import base64
import io
import json
import zipfile

import pytest


# 1x1 透明 PNG
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def _make_bank_zip(problems: list, images: dict = None) -> bytes:
    images = images or {}
    manifest = {
        "format": "oj-platform-bank",
        "format_version": 1,
        "app_version": "0.2.0",
        "problem_count": len(problems),
        "image_count": len(images),
        "categories": [{"name": "算法", "sort_order": 1}],
        "banks": [],
        "problems": problems,
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
        for name, content in images.items():
            zf.writestr(f"images/{name}", content)
    return buf.getvalue()


async def _upload(client, content: bytes, strategy: str = "skip"):
    files = {"file": ("bank.zip", content, "application/zip")}
    data = {"conflict_strategy": strategy}
    return await client.post(
        "/api/admin/bank/import",
        headers={"X-Admin-Key": "admin-key-change-me"},
        files=files,
        data=data,
    )


@pytest.mark.asyncio
async def test_import_basic(client):
    content = _make_bank_zip([
        {
            "title": "导入题 1",
            "category_name": "数学",
            "bank_name": "导入题库 A",
            "type": "algorithm",
            "difficulty": 1,
            "tags": ["测试"],
            "description": "描述",
            "answer": "答案",
            "explanation": None,
            "options": None,
            "blanks": None,
            "test_cases": [
                {"input_data": "1", "expected_output": "1", "is_example": True}
            ],
            "subprojects": [],
        },
        {
            "title": "导入题 2",
            "category_name": "算法",
            "bank_name": "导入题库 A",
            "type": "choice",
            "difficulty": 2,
            "tags": [],
            "description": "描述 2",
            "answer": None,
            "explanation": None,
            "options": [
                {"key": "A", "content": "a", "is_correct": True},
                {"key": "B", "content": "b", "is_correct": False},
            ],
            "blanks": None,
            "test_cases": [],
            "subprojects": [],
        },
    ])

    res = await _upload(client, content)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0
    assert data["failed"] == 0

    bres = await client.get("/api/banks")
    banks = bres.json()
    bank_a = next((b for b in banks if b["name"] == "导入题库 A"), None)
    assert bank_a is not None
    assert bank_a["problem_count"] == 2


@pytest.mark.asyncio
async def test_import_skip_conflict(client):
    content = _make_bank_zip([
        {
            "title": "重复题 X",
            "category_name": "算法",
            "type": "algorithm",
            "difficulty": 1,
            "description": "第一次",
            "test_cases": [],
            "subprojects": [],
        },
    ])
    res = await _upload(client, content)
    assert res.json()["imported"] == 1

    res2 = await _upload(client, content, strategy="skip")
    data = res2.json()
    assert data["imported"] == 0
    assert data["skipped"] == 1


@pytest.mark.asyncio
async def test_import_rename_conflict(client):
    content = _make_bank_zip([
        {
            "title": "重名题 Y",
            "category_name": "算法",
            "type": "algorithm",
            "difficulty": 1,
            "description": "内容",
            "test_cases": [],
            "subprojects": [],
        },
    ])
    await _upload(client, content)
    res = await _upload(client, content, strategy="rename")
    data = res.json()
    assert data["imported"] == 1

    pres = await client.get("/api/problems?keyword=重名题&page_size=50")
    titles = [p["title"] for p in pres.json()["items"]]
    assert "重名题 Y" in titles
    assert any(t.startswith("重名题 Y (导入") for t in titles)


@pytest.mark.asyncio
async def test_import_with_images(client):
    content = _make_bank_zip(
        problems=[
            {
                "title": "带图题 Z",
                "category_name": "算法",
                "type": "proof",
                "difficulty": 1,
                "description": "看图：![](images/abc.png)",
                "test_cases": [],
                "subprojects": [],
            },
        ],
        images={"abc.png": PNG_1X1},
    )
    res = await _upload(client, content)
    assert res.status_code == 200
    data = res.json()
    assert data["imported"] == 1

    pid = data["problem_ids"][0]
    detail = await client.get(f"/api/problems/{pid}")
    assert detail.status_code == 200
    assert "/api/images/" in detail.json()["description"]


@pytest.mark.asyncio
async def test_import_bad_zip(client):
    res = await client.post(
        "/api/admin/bank/import",
        headers={"X-Admin-Key": "admin-key-change-me"},
        files={"file": ("bad.zip", b"not a zip", "application/zip")},
        data={"conflict_strategy": "skip"},
    )
    assert res.status_code == 400