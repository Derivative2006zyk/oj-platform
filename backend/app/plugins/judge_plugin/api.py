from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.task_queue import enqueue
from app.database import get_db
from app.models.user import User
from app.plugins.judge_plugin import service
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionListResponse,
)


router = APIRouter(prefix="/api", tags=["submissions"])


@router.post(
    "/submissions",
    response_model=SubmissionDetail,
    status_code=status.HTTP_201_CREATED,
)
async def submit(
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交代码，写 DB 并入队。"""
    sub = await service.create_submission(db, current_user.id, data)

    await enqueue("judge_submit", submission_id=sub.id)

    return sub


@router.get("/submissions", response_model=SubmissionListResponse)
async def list_my_submissions(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户的提交列表。"""
    return await service.list_submissions_for_user(
        db, current_user.id, page, page_size
    )


@router.get("/submissions/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户的单条提交。他人提交返回 404。"""
    sub = await service.get_submission(db, submission_id)
    if sub is None or sub.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )
    return sub


@router.get(
    "/problems/{problem_id}/submissions",
    response_model=SubmissionListResponse,
)
async def list_problem_submissions(
    problem_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户在某个题目下的提交历史。"""
    return await service.list_submissions_for_problem(
        db, current_user.id, problem_id, page, page_size
    )