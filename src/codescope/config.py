from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    GITHUB_TOKEN: str
    LLM_API_KEY: str


settings = Config()
