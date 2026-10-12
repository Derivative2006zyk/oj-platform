from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.schemas.submission import SubmissionCreate


def _infer_submission_kind(language: str) -> str:
    if language == "choice":
        return "choice"
    if language == "fill_blank":
        return "fill_blank"
    return "code"


async def create_submission(
    db: AsyncSession,
    user_id: int,
    data: SubmissionCreate,
) -> Submission:
    """写 submissions 表，status=PENDING。"""
    kind = _infer_submission_kind(data.language)

    sub = Submission(
        user_id=user_id,
        problem_id=data.problem_id,
        submission_kind=kind,
        code=data.code,
        language=data.language,
        answer_data=data.answer_data,
        status="PENDING",
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def judge_inline(db: AsyncSession, sub: Submission) -> None:
    """同步判题：选择题。仅用于 submission_kind != code。"""
    from app.models.problem import Problem
    from app.plugins.judge_plugin.judge_choice import judge_choice
    from app.core.event_bus import get_event_bus
    from app.core.events import EventNames

    problem = await db.get(Problem, sub.problem_id)
    if problem is None:
        sub.status = "RE"
        sub.error_message = "Problem not found"
        await db.commit()
        await db.refresh(sub)
        return

    if sub.submission_kind == "choice":
        verdict = judge_choice(sub.answer_data, problem.options)
    elif sub.submission_kind == "fill_blank":
        verdict = {
            "status": "RE",
            "passed_cases": 0,
            "total_cases": 0,
            "runtime_ms": 0,
            "error_message": "fill_blank judge not implemented yet",
        }
    else:
        return

    sub.status = verdict["status"]
    sub.passed_cases = verdict["passed_cases"]
    sub.total_cases = verdict["total_cases"]
    sub.runtime_ms = verdict["runtime_ms"]
    sub.error_message = verdict.get("error_message")

    await db.commit()
    await db.refresh(sub)

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


async def get_submission(
    db: AsyncSession,
    submission_id: int,
) -> Optional[Submission]:
    return await db.get(Submission, submission_id)


async def list_submissions_for_user(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    problem_id: Optional[int] = None,
) -> dict:
    from sqlalchemy import func

    query = select(Submission).where(Submission.user_id == user_id)

    if status:
        query = query.where(Submission.status == status)
    if problem_id:
        query = query.where(Submission.problem_id == problem_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = (
        query.order_by(Submission.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


async def list_submissions_for_problem(
    db: AsyncSession,
    user_id: int,
    problem_id: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(Submission).where(
        Submission.user_id == user_id,
        Submission.problem_id == problem_id,
    )

    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = (
        query.order_by(Submission.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


async def get_widget_summary(db: AsyncSession, user_id: int) -> dict:
    """桌面小组件摘要数据。"""
    from datetime import datetime, timezone
    from sqlalchemy import func, distinct
    from app.models.problem import Problem

    total = (await db.execute(
        select(func.count()).where(Submission.user_id == user_id)
    )).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(
        tzinfo=None,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    today_count = (await db.execute(
        select(func.count()).where(
            Submission.user_id == user_id,
            Submission.created_at >= today_start,
        )
    )).scalar() or 0

    accepted = (await db.execute(
        select(func.count()).where(
            Submission.user_id == user_id,
            Submission.status == "AC",
        )
    )).scalar() or 0

    solved = (await db.execute(
        select(func.count(distinct(Submission.problem_id))).where(
            Submission.user_id == user_id,
            Submission.status == "AC",
        )
    )).scalar() or 0

    total_problems = (await db.execute(
        select(func.count()).select_from(Problem)
    )).scalar() or 0

    acceptance_rate = (accepted / total * 100) if total > 0 else 0.0

    latest_result = await db.execute(
        select(Submission)
        .where(Submission.user_id == user_id)
        .order_by(Submission.id.desc())
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()

    latest_info = None
    if latest is not None:
        latest_info = {
            "id": latest.id,
            "problem_id": latest.problem_id,
            "status": latest.status,
            "language": latest.language,
            "created_at": latest.created_at,
        }

    return {
        "total_submissions": total,
        "today_submissions": today_count,
        "total_accepted": accepted,
        "acceptance_rate": round(acceptance_rate, 2),
        "solved_problems": solved,
        "total_problems": total_problems,
        "latest_submission": latest_info,
    }