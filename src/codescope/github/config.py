from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitHubConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GITHUB_",
        extra="ignore",
    )

    token: SecretStr
    api_base_url: str = "https://api.github.com"
    api_version: str = "2026-03-10"
    user_agent: str = "codescope"
    requests_per_hour: int = 5000
    max_concurrent_requests: int = 10
    timeout_seconds: float = 10.0


@lru_cache(maxsize=1)
def get_github_config() -> GitHubConfig:
    return GitHubConfig()
