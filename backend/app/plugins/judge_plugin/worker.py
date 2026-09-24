from arq.connections import RedisSettings

from app.core.config import settings
from app.core.event_bus import get_event_bus
from app.core.events import EventNames


async def startup(ctx):
    """worker 启动时连 event_bus。"""
    bus = get_event_bus()
    await bus.connect()
    print("[worker] EventBus connected")


async def shutdown(ctx):
    """worker 关闭时断开 event_bus。"""
    bus = get_event_bus()
    await bus.disconnect()
    print("[worker] EventBus disconnected")


async def judge_submit(ctx, submission_id: int) -> None:
    """判题任务（今日占位：把 PENDING 改成 RE）。

    Day 7 起替换为真实沙箱判题。
    """
    from app.database import async_session
    from app.models.submission import Submission

    async with async_session() as db:
        sub = await db.get(Submission, submission_id)
        if sub is None:
            return

        # 占位逻辑：直接标 RE
        sub.status = "RE"
        sub.error_message = "Judge not implemented yet (Day 6 placeholder)"
        await db.commit()

        await get_event_bus().publish(
            EventNames.SUBMISSION_JUDGED,
            {
                "id": sub.id,
                "status": sub.status,
                "user_id": sub.user_id,
                "problem_id": sub.problem_id,
            },
        )


class WorkerSettings:
    functions = [judge_submit]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown