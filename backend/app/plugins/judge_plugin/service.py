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
) -> dict:
    query = select(Submission).where(Submission.user_id == user_id)

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