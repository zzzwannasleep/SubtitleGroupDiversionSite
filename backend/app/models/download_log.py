from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DownloadLog(Base):
    __tablename__ = "download_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    torrent_id: Mapped[int] = mapped_column(ForeignKey("torrents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    torrent: Mapped["Torrent"] = relationship(back_populates="download_logs")
    user: Mapped["User"] = relationship(back_populates="download_logs")


from app.models.torrent import Torrent
from app.models.user import User

