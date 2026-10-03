from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.password import hash_password, verify_password
from app.core.event_bus import get_event_bus
from app.core.events import EventNames
from app.models.user import User
from app.schemas.user import UserRegister


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    return await db.get(User, user_id)


async def create_user(db: AsyncSession, data: UserRegister) -> Optional[User]:
    """创建用户。用户名或邮箱已存在返回 None。"""
    if await get_user_by_username(db, data.username):
        return None
    if await get_user_by_email(db, data.email):
        return None

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 发布注册事件
    await get_event_bus().publish(
        EventNames.USER_REGISTERED,
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    )

    return user


async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """校验用户名密码。失败或已封禁返回 None。"""
    user = await get_user_by_username(db, username)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def change_password(
    db: AsyncSession,
    user: User,
    old_password: str,
    new_password: str,
) -> bool:
    from app.core.password import hash_password, verify_password

    if not verify_password(old_password, user.hashed_password):
        return False

    user.hashed_password = hash_password(new_password)
    await db.commit()
    return True


async def get_user_stats(db: AsyncSession, user_id: int) -> dict:
    from sqlalchemy import func, distinct
    from app.models.submission import Submission

    total = (await db.execute(
        select(func.count()).where(Submission.user_id == user_id)
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

    lang_rows = (await db.execute(
        select(Submission.language, func.count())
        .where(Submission.user_id == user_id)
        .group_by(Submission.language)
    )).all()
    language_distribution = {lang: cnt for lang, cnt in lang_rows}

    acceptance_rate = (accepted / total * 100) if total > 0 else 0.0

    return {
        "total_submissions": total,
        "accepted_submissions": accepted,
        "solved_problems": solved,
        "acceptance_rate": round(acceptance_rate, 2),
        "language_distribution": language_distribution,
    }

# ============ 管理员功能 ============

async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
) -> dict:
    """用户列表，支持筛选。"""
    from sqlalchemy import func, or_

    query = select(User)

    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            or_(User.username.ilike(pattern), User.email.ilike(pattern))
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = (
        query.order_by(User.id.asc())
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


async def update_user_role(
    db: AsyncSession,
    user_id: int,
    new_role: str,
    current_admin_id: int,
) -> Optional[User]:
    """修改用户角色。

    - 不能修改自己的角色（防止降级自己）
    - 目标用户不存在返回 None
    """
    if user_id == current_admin_id:
        raise ValueError("Cannot change your own role")

    user = await db.get(User, user_id)
    if user is None:
        return None

    user.role = new_role
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_status(
    db: AsyncSession,
    user_id: int,
    is_active: bool,
    current_admin_id: int,
) -> Optional[User]:
    """封禁/解封。

    - 不能封禁自己
    - 不能封禁最后一个 admin
    """
    if user_id == current_admin_id:
        raise ValueError("Cannot ban yourself")

    user = await db.get(User, user_id)
    if user is None:
        return None

    # 若封禁的是 admin，检查是否最后一个
    if not is_active and user.role == "admin":
        from sqlalchemy import func as sqlfunc
        admin_count = (await db.execute(
            select(sqlfunc.count()).where(
                User.role == "admin",
                User.is_active == True,
            )
        )).scalar() or 0
        if admin_count <= 1:
            raise ValueError("Cannot ban the last active admin")

    user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    return user


async def get_admin_stats(db: AsyncSession) -> dict:
    """全局统计。"""
    from sqlalchemy import func
    from app.models.submission import Submission
    from app.models.problem import Problem

    total_users = (await db.execute(
        select(func.count()).select_from(User)
    )).scalar() or 0

    total_admins = (await db.execute(
        select(func.count()).where(User.role == "admin")
    )).scalar() or 0

    active_users = (await db.execute(
        select(func.count()).where(User.is_active == True)
    )).scalar() or 0

    banned_users = total_users - active_users

    total_submissions = (await db.execute(
        select(func.count()).select_from(Submission)
    )).scalar() or 0

    total_accepted = (await db.execute(
        select(func.count()).where(Submission.status == "AC")
    )).scalar() or 0

    total_problems = (await db.execute(
        select(func.count()).select_from(Problem)
    )).scalar() or 0

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "active_users": active_users,
        "banned_users": banned_users,
        "total_submissions": total_submissions,
        "total_accepted": total_accepted,
        "total_problems": total_problems,
    }