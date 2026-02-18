from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "My FastAPI Project"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # DB
    DB_URL: str = "sqlite://db.sqlite3"
    DB_MODELS: list = ["app.models", "aerich.models"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 7
    LOG_DIR: str = "logs"

    # Proxy
    HTTP_PROXY: Optional[str] = None

    # Discord
    DISCORD_BOT_TOKEN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()