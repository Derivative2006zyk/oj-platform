from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import create_access_token
from app.core.security import get_current_user
from app.core.event_bus import get_event_bus
from app.core.events import EventNames
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    AdminStats,
    AdminUserItem,
    ChangePassword,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserRoleUpdate,
    UserStats,
    UserStatusUpdate,
)
from app.core.security import get_current_user, require_admin
from app.plugins.user_plugin import service
from typing import Optional


router = APIRouter(prefix="/api", tags=["users"])


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await service.create_user(db, data)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )
    return user


@router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await service.authenticate(db, data.username, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    await get_event_bus().publish(
        EventNames.USER_LOGGED_IN,
        {
            "id": user.id,
            "username": user.username,
        },
    )

    return TokenResponse(access_token=token)


@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/users/me/password")
async def change_password(
    data: ChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await service.change_password(
        db, current_user, data.old_password, data.new_password
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    return {"message": "Password updated"}


@router.get("/users/me/stats", response_model=UserStats)
async def get_my_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.get_user_stats(db, current_user.id)

# ============ 管理员功能 ============

admin_router = APIRouter(prefix="/api/admin", tags=["admin-users"])


@admin_router.get("/users")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """用户列表（管理员）。"""
    from typing import Optional as Opt

    result = await service.list_users(
        db, page, page_size, role=role, is_active=is_active, keyword=keyword
    )

    return {
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "items": [
            AdminUserItem.model_validate(u).model_dump()
            for u in result["items"]
        ],
    }


@admin_router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """修改用户角色。"""
    try:
        user = await service.update_user_role(
            db, user_id, data.role, current_admin.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return AdminUserItem.model_validate(user).model_dump()


@admin_router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """封禁/解封用户。"""
    try:
        user = await service.update_user_status(
            db, user_id, data.is_active, current_admin.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return AdminUserItem.model_validate(user).model_dump()


@admin_router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """全局统计（管理员）。"""
    return await service.get_admin_stats(db)