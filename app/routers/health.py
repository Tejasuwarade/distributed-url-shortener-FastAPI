from __future__ import annotations

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_db_session),
) -> HealthResponse:
    await session.execute(text("SELECT 1"))
    redis: Redis = get_redis()
    await redis.ping()
    return HealthResponse(status="ok", database="ok", redis="ok")
