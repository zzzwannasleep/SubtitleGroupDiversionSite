from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.types import bigint_type


class DownloadLog(Base):
    __tablename__ = "download_logs"

    id: Mapped[int] = mapped_column(bigint_type(), primary_key=True, autoincrement=True)
    torrent_id: Mapped[int] = mapped_column(
        bigint_type(),
        ForeignKey("torrents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        bigint_type(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    torrent: Mapped["Torrent"] = relationship(back_populates="download_logs")
    user: Mapped["User"] = relationship(back_populates="download_logs")


if TYPE_CHECKING:
    from app.models.torrent import Torrent
    from app.models.user import User
