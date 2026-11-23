import json
from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "BalanceUp API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    DATABASE_URL: str = (
        "postgresql+psycopg://balanceup:balanceup@localhost:5433/BalanceUp"
    )

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value


settings = Settings()
