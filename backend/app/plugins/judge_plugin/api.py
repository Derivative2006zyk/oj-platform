from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket, WebSocketDisconnect, Query

from app.core.jwt import decode_access_token
from app.core.ws_manager import get_ws_manager
from app.database import async_session

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

@router.websocket("/submissions/{submission_id}/ws")
async def submission_ws(
    websocket: WebSocket,
    submission_id: int,
    token: str = Query(...),
):
    """WebSocket 端点：推送某次提交的判题状态。

    鉴权：token 通过 query param 传入（浏览器 WS 不支持自定义 header）。
    校验：
    1. token 有效
    2. submission 属于 token 对应的用户
    """
    # 1. 解码 token
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id_str = payload.get("sub")
    if not user_id_str:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    user_id = int(user_id_str)

    # 2. 用独立 session 检查 submission 归属
    async with async_session() as db:
        sub = await service.get_submission(db, submission_id)
        if sub is None or sub.user_id != user_id:
            await websocket.close(code=4004, reason="Submission not found")
            return
        current_status = sub.status
        passed_cases = sub.passed_cases
        total_cases = sub.total_cases
        runtime_ms = sub.runtime_ms

    # 3. 注册连接
    manager = get_ws_manager()
    await manager.connect(user_id, websocket)

    try:
        # 立即发送当前状态
        await websocket.send_json({
            "type": "status",
            "submission_id": submission_id,
            "status": current_status,
            "passed_cases": passed_cases,
            "total_cases": total_cases,
            "runtime_ms": runtime_ms,
        })

        # 保持连接直到客户端关闭
        while True:
            # 接收客户端心跳/关闭信号（客户端可以定期发 ping）
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(user_id, websocket)