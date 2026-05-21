"""add user auth fields

Revision ID: 202605210003
Revises: 202605210002
Create Date: 2026-05-21 00:03:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605210003"
down_revision: str | None = "202605210002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = sa.Enum("USER", "ADMIN", name="user_role")


def upgrade() -> None:
    user_role.create(op.get_bind(), checkfirst=True)
    op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=False))
    op.add_column(
        "users",
        sa.Column("role", user_role, nullable=False, server_default="USER"),
    )
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "role")
    op.drop_column("users", "hashed_password")
    user_role.drop(op.get_bind(), checkfirst=True)
