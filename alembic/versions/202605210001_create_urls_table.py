"""create urls table

Revision ID: 202605210001
Revises:
Create Date: 2026-05-21 00:01:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605210001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "urls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_url", sa.String(length=2048), nullable=False),
        sa.Column("short_code", sa.String(length=32), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("short_code"),
    )
    op.create_index(op.f("ix_urls_id"), "urls", ["id"], unique=False)
    op.create_index(
        "ix_urls_short_code_active",
        "urls",
        ["short_code", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_urls_short_code_active", table_name="urls")
    op.drop_index(op.f("ix_urls_id"), table_name="urls")
    op.drop_table("urls")
