from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.types import bigint_type


class TrackerTorrentStatsCache(Base):
    __tablename__ = "tracker_torrent_stats_cache"

    torrent_id: Mapped[int] = mapped_column(
        bigint_type(),
        ForeignKey("torrents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    seeders: Mapped[int] = mapped_column(default=0, nullable=False)
    leechers: Mapped[int] = mapped_column(default=0, nullable=False)
    snatches: Mapped[int] = mapped_column(default=0, nullable=False)
    finished: Mapped[int] = mapped_column(default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="tracker", nullable=False)

    torrent: Mapped["Torrent"] = relationship(back_populates="stats_cache")


if TYPE_CHECKING:
    from app.models.torrent import Torrent
