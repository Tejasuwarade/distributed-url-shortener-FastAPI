from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Analytics(Base):
    __tablename__ = "analytics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    url_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    referer: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    url = relationship("URL", back_populates="analytics_events")

    __table_args__ = (
        Index("ix_analytics_url_clicked_at", "url_id", "clicked_at"),
        Index("ix_analytics_clicked_at", "clicked_at"),
        Index("ix_analytics_country_clicked_at", "country", "clicked_at"),
    )
