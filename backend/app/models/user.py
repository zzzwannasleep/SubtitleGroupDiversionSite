from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    UPLOADER = "uploader"
    USER = "user"


class UserStatus(str, Enum):
    ACTIVE = "active"
    BANNED = "banned"
    PENDING = "pending"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text(), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, native_enum=False), default=UserRole.USER, nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(UserStatus, native_enum=False),
        default=UserStatus.ACTIVE,
        nullable=False,
    )
    tracker_credential: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    rss_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    torrents: Mapped[list["Torrent"]] = relationship(back_populates="owner")
    download_logs: Mapped[list["DownloadLog"]] = relationship(back_populates="user")
    stats_cache: Mapped["TrackerUserStatsCache | None"] = relationship(back_populates="user", uselist=False)


if TYPE_CHECKING:
    from app.models.download_log import DownloadLog
    from app.models.torrent import Torrent
    from app.models.tracker_user_stats_cache import TrackerUserStatsCache
