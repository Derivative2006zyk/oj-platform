from fastapi import Header, HTTPException
from app.core.config import settings

async def verify_admin_key(x_admin_key: str = Header(None)):
    """验证管理员密钥，从请求头 X-Admin-Key 中获取"""
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="管理员密钥错误")
    return x_admin_key