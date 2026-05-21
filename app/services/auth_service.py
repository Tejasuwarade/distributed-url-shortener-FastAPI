from __future__ import annotations

import uuid

import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse


class AuthenticationError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = UserRepository(session)

    async def signup(self, email: str, password: str, name: str | None = None) -> User:
        existing_user = await self.repository.get_by_email(email)
        if existing_user is not None:
            raise UserAlreadyExistsError("User with this email already exists")

        try:
            return await self.repository.create(
                email=email,
                hashed_password=hash_password(password),
                name=name,
            )
        except IntegrityError as exc:
            raise UserAlreadyExistsError("User with this email already exists") from exc

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.repository.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        return self._tokens_for_user(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
            user_id = uuid.UUID(payload["sub"])
        except (jwt.InvalidTokenError, ValueError) as exc:
            raise AuthenticationError("Invalid refresh token") from exc

        user = await self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid refresh token")
        return self._tokens_for_user(user)

    @staticmethod
    def _tokens_for_user(user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id, user.role.value),
            expires_in=settings.access_token_expire_minutes * 60,
        )
