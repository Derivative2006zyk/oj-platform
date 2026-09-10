from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://oj:oj_password@localhost:5432/oj_platform"
    ADMIN_KEY: str = "admin-key-change-me"
    UPLOAD_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
    )
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)