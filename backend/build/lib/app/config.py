from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://erp:erp@localhost:5432/erp"
    secret_key: str = "dev-only-secret-change-me-before-any-real-use"
    access_token_minutes: int = 480

    first_owner_email: str = "owner@example.com"
    first_owner_password: str = "change-me"
    first_owner_name: str = "Owner"

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
