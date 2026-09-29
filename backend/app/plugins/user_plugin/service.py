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
    """校验用户名密码。失败返回 None。"""
    user = await get_user_by_username(db, username)
    if user is None:
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