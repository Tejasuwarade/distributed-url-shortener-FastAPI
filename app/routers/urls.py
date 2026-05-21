from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.url import URLCreateRequest, URLResponse, URLStatsResponse
from app.services.url_service import URLService

router = APIRouter(prefix="/urls")


@router.post(
    "",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_short_url(
    payload: URLCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> URLResponse:
    service = URLService(session=session, redis=get_redis())
    try:
        return await service.create_short_url(
            original_url=str(payload.original_url),
            user_id=current_user.id,
            custom_alias=payload.custom_alias,
            expires_at=payload.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{short_code}", response_model=URLStatsResponse)
async def get_url_stats(
    short_code: str,
    session: AsyncSession = Depends(get_db_session),
) -> URLStatsResponse:
    service = URLService(session=session, redis=get_redis())
    stats = await service.get_url_stats(short_code)
    if stats is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    return stats
