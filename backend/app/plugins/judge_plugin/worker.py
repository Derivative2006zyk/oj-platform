from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import settings
from app.core.event_bus import get_event_bus
from app.core.events import EventNames


async def startup(ctx):
    bus = get_event_bus()
    await bus.connect()
    print("[worker] EventBus connected")


async def shutdown(ctx):
    bus = get_event_bus()
    await bus.disconnect()
    print("[worker] EventBus disconnected")


async def judge_submit(ctx, submission_id: int) -> None:
    """判题任务。"""
    from app.database import async_session
    from app.models.submission import Submission
    from app.models.problem import Problem
    from app.models.test_case import TestCase
    from app.plugins.judge_plugin.judge_python import judge_python

    async with async_session() as db:
        sub = await db.get(Submission, submission_id)
        if sub is None:
            return

        # 只处理 PENDING
        if sub.status != "PENDING":
            return

        # 读测试点
        result = await db.execute(
            select(TestCase)
            .where(TestCase.problem_id == sub.problem_id)
            .order_by(TestCase.id)
        )
        test_cases = result.scalars().all()

        cases = [
            {
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_example": tc.is_example,
            }
            for tc in test_cases
        ]

        # 判题
        if sub.language == "python":
            verdict = judge_python(sub.code, cases)
        else:
            verdict = {
                "status": "RE",
                "passed_cases": 0,
                "total_cases": len(cases),
                "runtime_ms": 0,
                "error_message": f"Language not supported yet: {sub.language}",
            }

        sub.status = verdict["status"]
        sub.passed_cases = verdict["passed_cases"]
        sub.total_cases = verdict["total_cases"]
        sub.runtime_ms = verdict["runtime_ms"]
        sub.error_message = verdict.get("error_message")

        await db.commit()

        await get_event_bus().publish(
            EventNames.SUBMISSION_JUDGED,
            {
                "id": sub.id,
                "status": sub.status,
                "user_id": sub.user_id,
                "problem_id": sub.problem_id,
                "passed_cases": sub.passed_cases,
                "total_cases": sub.total_cases,
                "runtime_ms": sub.runtime_ms,
            },
        )


class WorkerSettings:
    functions = [judge_submit]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown