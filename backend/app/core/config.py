# backend/app/core/config.py

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str = "postgresql+asyncpg://oj:oj_password@localhost:5432/oj_platform"
    REDIS_URL: str = "redis://localhost:6379/0"
    EVENT_BUS_CHANNEL: str = "oj:events"
    ADMIN_KEY: str = "admin-key-change-me"
    UPLOAD_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
    )
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)