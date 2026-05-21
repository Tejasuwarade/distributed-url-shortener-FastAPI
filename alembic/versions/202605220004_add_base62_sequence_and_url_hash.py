"""add base62 sequence and url hash

Revision ID: 202605220004
Revises: 202605210003
Create Date: 2026-05-22 00:04:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605220004"
down_revision: str | None = "202605210003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS url_short_code_seq START WITH 100000")
    op.add_column(
        "urls",
        sa.Column(
            "original_url_hash",
            sa.String(length=64),
            nullable=False,
            server_default="",
        ),
    )
    op.alter_column("urls", "original_url_hash", server_default=None)
    op.create_index(
        "ix_urls_user_original_hash_active",
        "urls",
        ["user_id", "original_url_hash", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_urls_user_original_hash_active", table_name="urls")
    op.drop_column("urls", "original_url_hash")
    op.execute("DROP SEQUENCE IF EXISTS url_short_code_seq")
