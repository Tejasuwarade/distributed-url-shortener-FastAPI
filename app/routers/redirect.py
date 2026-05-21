from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.services.url_service import URLService

router = APIRouter()


@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_to_original_url(
    short_code: str,
    session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    service = URLService(session=session, redis=get_redis())
    original_url = await service.resolve_short_code(short_code)
    if original_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    return RedirectResponse(url=original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
