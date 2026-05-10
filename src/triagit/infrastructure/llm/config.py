from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LLM_",
        extra="ignore",
    )

    provider: Literal["anthropic", "openai"] = "anthropic"
    api_key: SecretStr
    model: str = "claude-haiku-4-5-20251001"
    max_concurrent_requests: int = 5
    daily_budget_usd: float = 5.0
    review_max_files: int = 8
    review_max_retries: int = 3


@lru_cache(maxsize=1)
def get_llm_config() -> LLMConfig:
    return LLMConfig()
