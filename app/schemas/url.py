from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

ALIAS_PATTERN = r"^[A-Za-z0-9_-]+$"


class URLCreateRequest(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern=ALIAS_PATTERN,
    )
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def validate_future_expiration(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        if value <= datetime.now(timezone.utc):
            raise ValueError("Expiration must be in the future")

        return value


class URLResponse(BaseModel):
    id: uuid.UUID
    original_url: str
    short_code: str
    custom_alias: str | None
    short_url: str
    expires_at: datetime | None
    is_duplicate: bool = False


class URLStatsResponse(BaseModel):
    id: uuid.UUID
    original_url: str
    short_code: str
    custom_alias: str | None
    short_url: str
    clicks: int
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
