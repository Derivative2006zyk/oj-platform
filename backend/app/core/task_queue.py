from typing import Any, Optional

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings


_pool: Optional[ArqRedis] = None


async def get_task_queue() -> ArqRedis:
    """获取 arq 连接池（懒加载单例）。"""
    global _pool
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    return _pool


async def enqueue(task_name: str, **kwargs: Any) -> Optional[str]:
    """投递任务到 arq 队列。返回 job_id 或 None。"""
    pool = await get_task_queue()
    job = await pool.enqueue_job(task_name, **kwargs)
    if job is None:
        return None
    return job.job_id


async def close_task_queue() -> None:
    """关闭 arq 连接池。"""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None