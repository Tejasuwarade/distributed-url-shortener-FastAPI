from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user


@router.get("/admin-check")
async def admin_check(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> dict[str, str]:
    return {"detail": f"Hello admin {current_user.email}"}
