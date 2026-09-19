import os
import logging
from typing import Optional
from backend.app.config import settings

logger = logging.getLogger("resqai.ai.client")


class AIClient:
    """Modular AI Client wrapper supporting LLM providers or rule-based heuristics fallback."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.GEMINI_API_KEY or settings.OPENAI_API_KEY or os.getenv("LLM_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.provider != "mock")


ai_client = AIClient()
