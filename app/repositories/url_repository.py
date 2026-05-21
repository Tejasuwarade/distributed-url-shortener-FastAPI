from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.url import URL


class URLRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        original_url: str,
        short_code: str,
        custom_alias: str | None = None,
        expires_at: datetime | None = None,
    ) -> URL:
        url = URL(
            original_url=original_url,
            short_code=short_code,
            custom_alias=custom_alias,
            expires_at=expires_at,
        )
        self.session.add(url)
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        await self.session.refresh(url)
        return url

    async def get_by_short_code(self, short_code: str) -> URL | None:
        result = await self.session.execute(
            select(URL).where(
                or_(URL.short_code == short_code, URL.custom_alias == short_code),
                URL.is_active.is_(True),
                or_(URL.expires_at.is_(None), URL.expires_at > func.now()),
            )
        )
        return result.scalar_one_or_none()

    async def code_or_alias_exists(self, value: str) -> bool:
        result = await self.session.execute(
            select(URL.id)
            .where(or_(URL.short_code == value, URL.custom_alias == value))
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def increment_clicks(self, url_id: uuid.UUID) -> None:
        await self.session.execute(
            update(URL).where(URL.id == url_id).values(clicks=URL.clicks + 1)
        )
        await self.session.commit()
