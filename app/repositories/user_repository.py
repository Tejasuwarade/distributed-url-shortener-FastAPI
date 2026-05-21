from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        email: str,
        hashed_password: str,
        name: str | None = None,
        role: UserRole = UserRole.USER,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            name=name,
            role=role,
        )
        self.session.add(user)
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
