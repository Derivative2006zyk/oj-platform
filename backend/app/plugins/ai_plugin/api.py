from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.user_ai_config import UserAIConfig
from app.core.security import get_current_user
from app.plugins.ai_plugin.backend import MockAIBackend, OpenAICompatibleBackend

router = APIRouter(prefix="/api/plugins/ai", tags=["ai"])

class ConfigUpdateRequest(BaseModel):
    config: dict

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

# 获取当前用户的配置
@router.get("/config")
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserAIConfig).where(UserAIConfig.user_id == current_user.id))
    user_config = result.scalar_one_or_none()
    return {"config": user_config.config if user_config else {}}

# 保存当前用户的配置
@router.put("/config")
async def save_ai_config(
    req: ConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserAIConfig).where(UserAIConfig.user_id == current_user.id))
    user_config = result.scalar_one_or_none()
    
    if user_config:
        user_config.config = req.config
    else:
        user_config = UserAIConfig(user_id=current_user.id, config=req.config)
        db.add(user_config)
        
    await db.commit()
    return {"message": "success"}

# 聊天接口（根据当前登录用户读取配置）
@router.post("/chat")
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserAIConfig).where(UserAIConfig.user_id == current_user.id))
    user_config = result.scalar_one_or_none()
    config = user_config.config if user_config else {}
    
    profiles = config.get("profiles", {})
    current_profile_name = config.get("current_profile", "")
    
    active = profiles.get(current_profile_name, {})
    api_key = (active.get("api_key") or "").strip()
    base_url = (active.get("base_url") or "https://api.deepseek.com").strip()
    model_name = (active.get("model") or "deepseek-chat").strip()
    system_prompt = (active.get("system_prompt") or "你是一个专业的编程与数学助教。").strip()
    
    final_messages = [{"role": "system", "content": system_prompt}] + req.messages
    
    if api_key:
        backend = OpenAICompatibleBackend(api_key, base_url, model_name)
    else:
        backend = MockAIBackend()

    async def event_generator():
        try:
            yield ": keep-alive\n\n"
            async for chunk in backend.chat_stream(final_messages):
                for line in chunk.split('\n'):
                    yield f"data: {line}\n"
                yield "\n"
        except Exception as e:
            yield f"data: 【流式异常】{str(e)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")