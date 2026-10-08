from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.schemas.submission import SubmissionCreate


async def create_submission(
    db: AsyncSession,
    user_id: int,
    data: SubmissionCreate,
) -> Submission:
    """写 submissions 表，status=PENDING。"""
    sub = Submission(
        user_id=user_id,
        problem_id=data.problem_id,
        code=data.code,
        language=data.language,
        status="PENDING",
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


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

    # 1. 总提交数
    total = (await db.execute(
        select(func.count()).where(Submission.user_id == user_id)
    )).scalar() or 0

    # 2. 今日提交数（UTC 当日 0 点起）
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

    # 3. AC 数
    accepted = (await db.execute(
        select(func.count()).where(
            Submission.user_id == user_id,
            Submission.status == "AC",
        )
    )).scalar() or 0

    # 4. 已解题数（distinct problem_id 且 AC）
    solved = (await db.execute(
        select(func.count(distinct(Submission.problem_id))).where(
            Submission.user_id == user_id,
            Submission.status == "AC",
        )
    )).scalar() or 0

    # 5. 题目总数
    total_problems = (await db.execute(
        select(func.count()).select_from(Problem)
    )).scalar() or 0

    # 6. 通过率
    acceptance_rate = (accepted / total * 100) if total > 0 else 0.0

    # 7. 最近一次提交
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