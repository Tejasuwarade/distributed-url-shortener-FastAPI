from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.url_repository import URLRepository
from app.schemas.url import URLResponse, URLStatsResponse
from app.utils.short_code import generate_short_code


class URLService:
    CACHE_TTL_SECONDS = 60 * 60 * 24

    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.repository = URLRepository(session)
        self.redis = redis

    async def create_short_url(
        self,
        original_url: str,
        user_id: uuid.UUID | None = None,
        custom_alias: str | None = None,
        expires_at: datetime | None = None,
    ) -> URLResponse:
        if custom_alias and await self.repository.code_or_alias_exists(custom_alias):
            raise ValueError("Custom alias is already in use")

        url = None
        for _ in range(10):
            short_code = await self._generate_unique_short_code()
            try:
                url = await self.repository.create(
                    original_url=original_url,
                    short_code=short_code,
                    user_id=user_id,
                    custom_alias=custom_alias,
                    expires_at=expires_at,
                )
                break
            except IntegrityError:
                continue

        if url is None:
            raise RuntimeError("Unable to create unique short URL")

        await self._cache_url(url.id, url.short_code, url.original_url, url.expires_at)
        if url.custom_alias:
            await self._cache_url(url.id, url.custom_alias, url.original_url, url.expires_at)

        return URLResponse(
            id=url.id,
            original_url=url.original_url,
            short_code=url.short_code,
            custom_alias=url.custom_alias,
            short_url=self._build_short_url(url.custom_alias or url.short_code),
            expires_at=url.expires_at,
        )

    async def resolve_short_code(self, short_code: str) -> str | None:
        cache_key = self._cache_key(short_code)
        cached_payload = await self.redis.get(cache_key)
        if cached_payload:
            cached_url = json.loads(cached_payload)
            expires_at = cached_url.get("expires_at")
            if expires_at and self._to_aware_utc(datetime.fromisoformat(expires_at)) <= datetime.now(
                timezone.utc
            ):
                await self.redis.delete(cache_key)
                return None
            await self.repository.increment_clicks(uuid.UUID(cached_url["id"]))
            return cached_url["original_url"]

        url = await self.repository.get_by_short_code(short_code)
        if url is None:
            return None

        await self.repository.increment_clicks(url.id)
        await self._cache_url(url.id, short_code, url.original_url, url.expires_at)
        return url.original_url

    async def get_url_stats(self, short_code: str) -> URLStatsResponse | None:
        url = await self.repository.get_by_short_code(short_code)
        if url is None:
            return None

        return URLStatsResponse(
            id=url.id,
            original_url=url.original_url,
            short_code=url.short_code,
            custom_alias=url.custom_alias,
            short_url=self._build_short_url(url.custom_alias or url.short_code),
            clicks=url.clicks,
            is_active=url.is_active,
            expires_at=url.expires_at,
            created_at=url.created_at,
            updated_at=url.updated_at,
        )

    async def _generate_unique_short_code(self) -> str:
        for _ in range(10):
            short_code = generate_short_code(settings.short_code_length)
            if not await self.repository.code_or_alias_exists(short_code):
                return short_code
        raise RuntimeError("Unable to generate unique short code")

    @staticmethod
    def _cache_key(short_code: str) -> str:
        return f"url:{short_code}"

    async def _cache_url(
        self,
        url_id: uuid.UUID,
        short_code: str,
        original_url: str,
        expires_at: datetime | None,
    ) -> None:
        ttl = self.CACHE_TTL_SECONDS
        if expires_at is not None:
            expires_at = self._to_aware_utc(expires_at)
            ttl = min(ttl, max(1, int((expires_at - datetime.now(timezone.utc)).total_seconds())))

        await self.redis.setex(
            self._cache_key(short_code),
            ttl,
            json.dumps(
                {
                    "id": str(url_id),
                    "original_url": original_url,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                }
            ),
        )

    @staticmethod
    def _build_short_url(short_code: str) -> str:
        return f"{settings.base_url}/{short_code}"

    @staticmethod
    def _to_aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
