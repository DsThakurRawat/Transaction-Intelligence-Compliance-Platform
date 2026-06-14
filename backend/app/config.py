from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Local SQLite by default (zero infra). Override with DATABASE_URL when
    # deploying (Postgres) or in tests (a temp file). Swap happens in config,
    # never in code.
    database_url: str = "sqlite:///txn.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
