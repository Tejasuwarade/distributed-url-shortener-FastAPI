from __future__ import annotations

from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Distributed URL Shortener"
    app_env: str = "local"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(..., validation_alias="DATABASE_URL")
    redis_url: str = Field(..., validation_alias="REDIS_URL")

    base_url: str = "http://localhost:8000"
    short_code_length: int = 8
    log_level: str = "INFO"
    jwt_secret_key: str = "change-me-generate-a-strong-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        PostgresDsn(value)
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        RedisDsn(value)
        return value

    @field_validator("base_url")
    @classmethod
    def strip_base_url(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
