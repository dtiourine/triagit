from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LLM_",
        extra="ignore",
    )

    api_key: SecretStr
    # base_url: str = "https://api.together.xyz/v1"
    # model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    max_concurrent_requests: int = 5
    daily_budget_usd: float = 5.0
    review_max_files: int = 8
    review_max_retries: int = 3


@lru_cache(maxsize=1)
def get_llm_config() -> LLMConfig:
    return LLMConfig()
