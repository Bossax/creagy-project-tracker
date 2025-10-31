"""Application configuration utilities."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass
class Settings:
    """Settings loaded from environment variables for database configuration."""

    postgres_host: str = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.environ.get("POSTGRES_PORT", "5432"))
    postgres_user: str = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password: str = os.environ.get("POSTGRES_PASSWORD", "postgres")
    postgres_db: str = os.environ.get("POSTGRES_DB", "postgres")

    @property
    def database_url(self) -> str:
        """Construct a SQLAlchemy-compatible database URL."""

        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
