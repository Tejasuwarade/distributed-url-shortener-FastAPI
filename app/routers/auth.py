from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
)
from app.services.auth_service import AuthenticationError, AuthService, UserAlreadyExistsError

router = APIRouter(prefix="/auth")


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: UserSignupRequest,
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    service = AuthService(session)
    try:
        return await service.signup(
            email=str(payload.email),
            password=payload.password,
            name=payload.name,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    service = AuthService(session)
    try:
        return await service.login(email=str(payload.email), password=payload.password)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    service = AuthService(session)
    try:
        return await service.refresh(payload.refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
