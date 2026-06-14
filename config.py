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

    # Rule Engine Config
    rule_amount_threshold_usd: float = 5000.0
    rule_amount_threshold_inr: float = 400000.0
    
    rule_velocity_window_minutes: int = 15
    rule_velocity_count: int = 5
    
    # AML structuring config
    rule_structuring_threshold_usd: float = 10000.0
    rule_structuring_threshold_inr: float = 800000.0
    rule_structuring_window_hours: int = 72
    
    rule_odd_hour_start: int = 2
    rule_odd_hour_end: int = 5
    
    rule_high_risk_mcc: list[str] = ["5999", "6011", "6012"]
    
    # Scoring Config
    scoring_rule_weights: dict[str, int] = {
        "velocity": 40,
        "structuring": 40,
        "amount": 25,
        "amount_deviation": 25,
        "new_country": 25,
        "new_mcc": 15,
        "high_risk_mcc": 10,
        "odd_hour": 5,
        "ml_ensemble": 40
    }
    scoring_band_low: int = 25
    scoring_band_medium: int = 50
    scoring_band_high: int = 75


@lru_cache
def get_settings() -> Settings:
    return Settings()
