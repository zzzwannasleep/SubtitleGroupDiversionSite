from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TrackerUserStatsCache(Base):
    __tablename__ = "tracker_user_stats_cache"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    uploaded_bytes: Mapped[int] = mapped_column(default=0, nullable=False)
    downloaded_bytes: Mapped[int] = mapped_column(default=0, nullable=False)
    ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="tracker", nullable=False)

    user: Mapped["User"] = relationship(back_populates="stats_cache")


if TYPE_CHECKING:
    from app.models.user import User
