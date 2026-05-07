from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class GlobalConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: PostgresDsn
    redis_url: RedisDsn

    max_concurrent_github_requests: int = 10
    max_concurrent_llm_requests: int = 5
    daily_llm_budget_usd: float = 5.0
    per_ip_daily_analyses: int = 5


settings = GlobalConfig()
