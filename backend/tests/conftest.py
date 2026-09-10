import os
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = (
    os.environ.get("TEST_DATABASE_URL")
    or "postgresql+asyncpg://oj:oj_password@localhost:5432/oj_platform_test"
)

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import Base, engine, async_session
from app.models.category import Category


@pytest.fixture(autouse=True)
async def setup_database():
    """
    每个测试前：
      1. 删表（清空历史数据）
      2. 建表
      3. 预置 5 个分类
    每个测试后：删表
    """
    # 清空 + 建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 预置分类
    async with async_session() as session:
        session.add_all([
            Category(name="算法", sort_order=1),
            Category(name="数学", sort_order=2),
            Category(name="物理", sort_order=3),
            Category(name="英语", sort_order=4),
            Category(name="其他", sort_order=99),
        ])
        await session.commit()

    yield

    # 测试后清空
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """提供一个异步 httpx 客户端，直接调用 FastAPI 应用"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c