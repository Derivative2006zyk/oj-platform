from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt import decode_access_token
from app.database import get_db
from app.models.user import User


# ============ 管理员密钥校验（0.1 保留） ============

async def verify_admin_key(x_admin_key: str = Header(None, alias="X-Admin-Key")):
    if not x_admin_key or x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return x_admin_key


# ============ JWT 鉴权 ============

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT 中解析用户。无 token 或无效时返回 401。"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await db.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求当前用户是 admin。"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privilege required")
    return current_user