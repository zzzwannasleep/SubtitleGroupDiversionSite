from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.types import bigint_type


class Torrent(Base):
    __tablename__ = "torrents"

    id: Mapped[int] = mapped_column(bigint_type(), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    info_hash: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    owner_id: Mapped[int] = mapped_column(bigint_type(), ForeignKey("users.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(bigint_type(), ForeignKey("categories.id"), nullable=False, index=True)
    torrent_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    cover_image_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    nfo_text: Mapped[str] = mapped_column(Text, nullable=True)
    media_info: Mapped[str] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(back_populates="torrents")
    category: Mapped["Category"] = relationship(back_populates="torrents")
    files: Mapped[list["TorrentFile"]] = relationship(back_populates="torrent", cascade="all, delete-orphan")
    download_logs: Mapped[list["DownloadLog"]] = relationship(back_populates="torrent")
    stats_cache: Mapped["TrackerTorrentStatsCache"] = relationship(back_populates="torrent", uselist=False)


if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.download_log import DownloadLog
    from app.models.torrent_file import TorrentFile
    from app.models.tracker_torrent_stats_cache import TrackerTorrentStatsCache
    from app.models.user import User
