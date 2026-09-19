import os
from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ResQAI - Intelligent Emergency Response & Resource Coordination"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB Configuration (Strictly MongoDB ONLY)
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "resqai"
    
    # Backward compatibility alias
    MONGODB_URL: str = ""
    MONGODB_DB_NAME: str = ""
    
    @property
    def mongo_uri(self) -> str:
        return self.MONGODB_URI or self.MONGODB_URL or os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017"

    @property
    def mongo_db_name(self) -> str:
        return self.MONGODB_DATABASE or self.MONGODB_DB_NAME or os.getenv("MONGODB_DATABASE") or os.getenv("MONGODB_DB_NAME") or "resqai"

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            if self.CORS_ORIGINS.startswith("[") and self.CORS_ORIGINS.endswith("]"):
                import json
                try:
                    return json.loads(self.CORS_ORIGINS)
                except Exception:
                    pass
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return ["*"]

    # AI / LLM Configuration
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_BASE_URL: Optional[str] = None
    ENABLE_AI_ANALYSIS: bool = True
    
    # Backward compatibility aliases
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "auto"

    @property
    def effective_ai_key(self) -> str:
        return self.AI_API_KEY or self.OPENAI_API_KEY or self.GEMINI_API_KEY or os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    
    # Real-time WebSocket Configuration
    WS_HEARTBEAT_SEC: int = 15
    
    # Authentication & JWT Configuration
    JWT_SECRET_KEY: str = "resqai-emergency-command-secret-key-2026-jwt-token"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    DEMO_DEFAULT_PASSWORD: str = "ResQAI@2026!"
    
    # Duplicate Detection thresholds
    DISTANCE_THRESHOLD_KM: float = 1.0
    TIME_THRESHOLD_MINUTES: int = 45
    TEXT_SIMILARITY_THRESHOLD: float = 0.80
    
    # Backward compatibility aliases
    DEDUP_DISTANCE_THRESHOLD_KM: float = 1.0
    DEDUP_TIME_WINDOW_MINUTES: int = 45

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()
