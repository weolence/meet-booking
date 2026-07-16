from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return int(raw_value)


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    database_url: str
    db_echo: bool
    db_pool_size: int
    db_max_overflow: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "meet-booking"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@postgres:5432/meet_booking",
        ),
        db_echo=_env_bool("DB_ECHO", False),
        db_pool_size=_env_int("DB_POOL_SIZE", 10),
        db_max_overflow=_env_int("DB_MAX_OVERFLOW", 20),
    )
