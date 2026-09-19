from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "resqai"

    LLM_PROVIDER: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: Optional[str] = None

    FRONTEND_ORIGIN: str = "http://localhost:3000"

    DEDUP_DISTANCE_KM: float = 1.0
    DEDUP_WINDOW_MIN: int = 45
    DEDUP_SIM_THRESHOLD: float = 0.35
    DELAY_ALERT_MIN: int = 10
    ESCALATION_MIN: int = 20
    DEMO_MODE: bool = False
    DEMO_TIME_SCALE: float = 1.0


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()
