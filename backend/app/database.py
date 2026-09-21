# backend/app/database.py

import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from app.core.config import settings


# 测试环境用 NullPool，避免连接跨事件循环复用
if os.environ.get("TESTING"):
    _poolclass = NullPool
else:
    _poolclass = AsyncAdaptedQueuePool


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=_poolclass,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session