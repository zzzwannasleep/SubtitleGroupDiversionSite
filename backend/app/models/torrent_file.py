from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TorrentFile(Base):
    __tablename__ = "torrent_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    torrent_id: Mapped[int] = mapped_column(ForeignKey("torrents.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)

    torrent: Mapped["Torrent"] = relationship(back_populates="files")


if TYPE_CHECKING:
    from app.models.torrent import Torrent
