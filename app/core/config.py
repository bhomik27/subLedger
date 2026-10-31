from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based settings. Values come from env vars, then .env, then defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SubLedger"
    database_url: str = "sqlite:///./subledger.db"
    sql_echo: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
