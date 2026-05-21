from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class URLCreateRequest(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = Field(default=None, min_length=3, max_length=64)
    expires_at: datetime | None = None


class URLResponse(BaseModel):
    id: uuid.UUID
    original_url: str
    short_code: str
    custom_alias: str | None
    short_url: str
    expires_at: datetime | None


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
