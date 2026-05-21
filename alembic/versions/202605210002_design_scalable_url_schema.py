"""design scalable url shortener schema

Revision ID: 202605210002
Revises: 202605210001
Create Date: 2026-05-21 00:02:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202605210002"
down_revision: str | None = "202605210001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_urls_short_code_active", table_name="urls")
    op.drop_index(op.f("ix_urls_id"), table_name="urls")
    op.drop_table("urls")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
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
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index(
        "ix_users_active_created_at",
        "users",
        ["is_active", "created_at"],
        unique=False,
    )

    op.create_table(
        "urls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_url", sa.String(length=2048), nullable=False),
        sa.Column("short_code", sa.String(length=32), nullable=False),
        sa.Column("custom_alias", sa.String(length=64), nullable=True),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("custom_alias"),
        sa.UniqueConstraint("short_code"),
    )
    op.create_index("ix_urls_short_code", "urls", ["short_code"], unique=False)
    op.create_index("ix_urls_custom_alias", "urls", ["custom_alias"], unique=False)
    op.create_index(
        "ix_urls_lookup_active",
        "urls",
        ["short_code", "is_active", "expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_urls_user_created_at",
        "urls",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_urls_expires_at",
        "urls",
        ["expires_at"],
        unique=False,
        postgresql_where=sa.text("expires_at IS NOT NULL"),
    )

    op.create_table(
        "analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "clicked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("referer", sa.String(length=2048), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("device_type", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["url_id"], ["urls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analytics_url_clicked_at",
        "analytics",
        ["url_id", "clicked_at"],
        unique=False,
    )
    op.create_index("ix_analytics_clicked_at", "analytics", ["clicked_at"], unique=False)
    op.create_index(
        "ix_analytics_country_clicked_at",
        "analytics",
        ["country", "clicked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_analytics_country_clicked_at", table_name="analytics")
    op.drop_index("ix_analytics_clicked_at", table_name="analytics")
    op.drop_index("ix_analytics_url_clicked_at", table_name="analytics")
    op.drop_table("analytics")

    op.drop_index("ix_urls_expires_at", table_name="urls")
    op.drop_index("ix_urls_user_created_at", table_name="urls")
    op.drop_index("ix_urls_lookup_active", table_name="urls")
    op.drop_index("ix_urls_custom_alias", table_name="urls")
    op.drop_index("ix_urls_short_code", table_name="urls")
    op.drop_table("urls")

    op.drop_index("ix_users_active_created_at", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

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
