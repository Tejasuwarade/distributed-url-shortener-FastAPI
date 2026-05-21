from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ShortCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def next_seed(self) -> int:
        result = await self.session.execute(text("SELECT nextval('url_short_code_seq')"))
        return int(result.scalar_one())
