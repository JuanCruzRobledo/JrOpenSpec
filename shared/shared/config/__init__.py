"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://buensabor:changeme@localhost:5432/buensabor"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/api"

    # JWT / Auth
    JWT_SECRET: str = "change-me-in-production-min-32-chars!"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # Table Token (HMAC-SHA256)
    TABLE_TOKEN_SECRET: str = "change-me-table-token-secret-32ch!"

    # CORS
    CORS_ORIGINS: str = ""

    # Cookie settings
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance cached via lru_cache."""
    return Settings()


settings = get_settings()
