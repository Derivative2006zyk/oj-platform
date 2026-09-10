import pytest
from app.core.config import settings

# 管理员请求头
ADMIN_HEADERS = {"X-Admin-Key": settings.ADMIN_KEY}

def make_problem(**overrides):
    """生成一个算法题请求体的默认模板，可通过 overrides 覆盖部分字段"""
    data = {
        "title": "两数之和",
        "category_id": 1,
        "description": "给定一个整数数组，找出和为目标值的两个数。",
        "type": "algorithm",
        "difficulty": 1,
        "tags": ["数组", "哈希表"],
        "answer": "```python\ndef two_sum(nums, target):\n    ...\n```",
        "test_cases": [
            {
                "input_data": "[2,7,11,15]\n9",
                "expected_output": "[0,1]",
                "is_example": True,
            }
        ],
    }
    data.update(overrides)
    return data

# 分类测试
@pytest.mark.asyncio
async def test_get_categories(client):
    """分类接口应返回5条预置分类"""
    res = await client.get("/api/categories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    assert data[0]["name"] == "算法"

# 鉴权测试
@pytest.mark.asyncio
async def test_create_problem_requires_admin_key(client):
    """不带管理员密钥应返回403"""
    res = await client.post("/api/admin/problems", json=make_problem())
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_create_problem_wrong_admin_key(client):
    """错误的密钥应返回403"""
    res = await client.post(
        "/api/admin/problems",
        json=make_problem(),
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert res.status_code == 403

# 算法题测试
@pytest.mark.asyncio
async def test_create_algorithm_problem(client):
    """创建算法题应返回201"""
    res = await client.post(
        "/api/admin/problems", json=make_problem(), headers=ADMIN_HEADERS
    )
    assert res.status_code == 201
    assert res.json()["id"] == 1

# 选择题测试
@pytest.mark.asyncio
async def test_create_choice_problem(client):
    """创建选择题（含选项）"""
    data = make_problem(
        title="以下哪个不是排序算法？",
        type="choice",
        options=[
            {"key": "A", "content": "快速排序", "is_correct": False},
            {"key": "B", "content": "冒泡排序", "is_correct": False},
            {"key": "C", "content": "二分查找", "is_correct": True},
            {"key": "D", "content": "归并排序", "is_correct": False},
        ],
        test_cases=[],
    )
    res = await client.post("/api/admin/problems", json=data, headers=ADMIN_HEADERS)
    assert res.status_code == 201
    pid = res.json()["id"]

    # 详情应包含 options
    detail = await client.get(f"/api/problems/{pid}")
    assert detail.status_code == 200
    body = detail.json()
    assert len(body["options"]) == 4
    assert body["options"][2]["key"] == "C"
    assert body["options"][2]["is_correct"] is True

# 科研项目测试
@pytest.mark.asyncio
async def test_create_research_problem(client):
    """创建科研项目题（含子项目）"""
    data = make_problem(
        title="让Transformer学会做数学题",
        type="research",
        test_cases=[],
        subprojects=[
            {
                "title": "数据准备",
                "description": "准备训练数据",
                "hint": "先看看已有数据集",
                "reference_links": [
                    {"title": "论文1", "url": "https://arxiv.org/abs/xxx"}
                ],
                "sort_order": 1,
            },
            {
                "title": "模型训练",
                "description": "训练一个模型",
                "sort_order": 2,
            },
        ],
    )
    res = await client.post("/api/admin/problems", json=data, headers=ADMIN_HEADERS)
    assert res.status_code == 201
    pid = res.json()["id"]

    # 详情应包含 subprojects，并按 sort_order 排序
    detail = await client.get(f"/api/problems/{pid}")
    assert detail.status_code == 200
    body = detail.json()
    assert len(body["subprojects"]) == 2
    assert body["subprojects"][0]["title"] == "数据准备"
    assert body["subprojects"][1]["title"] == "模型训练"

# 详情不泄露答案
@pytest.mark.asyncio
async def test_problem_detail_does_not_expose_answer(client):
    """详情接口不应返回答案字段"""
    await client.post(
        "/api/admin/problems", json=make_problem(), headers=ADMIN_HEADERS
    )
    res = await client.get("/api/problems/1")
    assert res.status_code == 200
    body = res.json()
    # 详情里不应有 answer
    assert "answer" not in body

# 查看答案接口
@pytest.mark.asyncio
async def test_get_answer(client):
    """查看答案接口应返回答案和解析"""
    await client.post(
        "/api/admin/problems", json=make_problem(), headers=ADMIN_HEADERS
    )
    res = await client.get("/api/problems/1/answer")
    assert res.status_code == 200
    body = res.json()
    assert body["answer"] is not None
    assert "two_sum" in body["answer"]

# 删除题目
@pytest.mark.asyncio
async def test_delete_problem(client):
    """删除后应查询不到"""
    await client.post(
        "/api/admin/problems", json=make_problem(), headers=ADMIN_HEADERS
    )
    res = await client.delete("/api/admin/problems/1", headers=ADMIN_HEADERS)
    assert res.status_code == 200
    res = await client.get("/api/problems/1")
    assert res.status_code == 404

# 题目列表
@pytest.mark.asyncio
async def test_list_problems(client):
    """创建两个题目，列表应返回2条"""
    await client.post(
        "/api/admin/problems", json=make_problem(title="题1"), headers=ADMIN_HEADERS
    )
    await client.post(
        "/api/admin/problems", json=make_problem(title="题2"), headers=ADMIN_HEADERS
    )
    res = await client.get("/api/problems")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2

# 标签接口
@pytest.mark.asyncio
async def test_get_tags(client):
    """创建带标签的题目后，标签接口应返回对应标签"""
    await client.post(
        "/api/admin/problems", json=make_problem(), headers=ADMIN_HEADERS
    )
    res = await client.get("/api/tags")
    assert res.status_code == 200
    tags = res.json()
    assert "数组" in tags
    assert "哈希表" in tags