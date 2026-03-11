from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.category import Category
from app.models.torrent import Torrent
from app.models.torrent_file import TorrentFile
from app.models.tracker_torrent_stats_cache import TrackerTorrentStatsCache
from app.models.user import User
from app.services.torrent_parse_service import ParsedTorrent, TorrentParseError, parse_torrent_bytes


class TorrentUploadError(ValueError):
    """Raised when a torrent upload fails validation."""


MAX_TORRENT_FILE_SIZE = 10 * 1024 * 1024


def _validate_cover_image_url(cover_image_url: str | None) -> str | None:
    if cover_image_url is None:
        return None
    value = cover_image_url.strip()
    if not value:
        return None
    if not (value.startswith("http://") or value.startswith("https://")):
        raise TorrentUploadError("Cover image URL must start with http:// or https://")
    return value


def _validate_upload_file(filename: str | None, file_bytes: bytes) -> None:
    if not filename or not filename.lower().endswith(".torrent"):
        raise TorrentUploadError("Uploaded file must use the .torrent extension")
    if not file_bytes:
        raise TorrentUploadError("Uploaded file is empty")
    if len(file_bytes) > MAX_TORRENT_FILE_SIZE:
        raise TorrentUploadError("Uploaded .torrent file exceeds the 10 MiB size limit")


def _ensure_category_exists(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None or not category.is_enabled:
        raise TorrentUploadError("Selected category does not exist or is disabled")
    return category


def _ensure_not_duplicate(db: Session, info_hash: str) -> None:
    duplicate = db.scalar(select(Torrent.id).where(Torrent.info_hash == info_hash))
    if duplicate is not None:
        raise TorrentUploadError("A torrent with the same info_hash already exists")


def _persist_original_torrent(info_hash: str, file_bytes: bytes) -> Path:
    settings = get_settings()
    storage_dir = Path(settings.torrent_storage_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    torrent_path = storage_dir / f"{info_hash}.torrent"
    torrent_path.write_bytes(file_bytes)
    return torrent_path


def create_uploaded_torrent(
    db: Session,
    *,
    current_user: User,
    filename: str | None,
    file_bytes: bytes,
    category_id: int,
    name: str | None,
    subtitle: str | None,
    description: str | None,
    cover_image_url: str | None,
    media_info: str | None,
) -> tuple[Torrent, ParsedTorrent]:
    _validate_upload_file(filename, file_bytes)
    _ensure_category_exists(db, category_id)

    try:
        parsed = parse_torrent_bytes(file_bytes)
    except TorrentParseError as exc:
        raise TorrentUploadError(str(exc)) from exc

    _ensure_not_duplicate(db, parsed.info_hash)
    normalized_cover_url = _validate_cover_image_url(cover_image_url)

    saved_path = _persist_original_torrent(parsed.info_hash, file_bytes)
    try:
        torrent = Torrent(
            name=name.strip() if name and name.strip() else parsed.torrent_name,
            subtitle=subtitle.strip() if subtitle and subtitle.strip() else None,
            description=description.strip() if description and description.strip() else None,
            info_hash=parsed.info_hash,
            size_bytes=parsed.size_bytes,
            owner_id=current_user.id,
            category_id=category_id,
            torrent_path=str(saved_path),
            cover_image_url=normalized_cover_url,
            media_info=media_info.strip() if media_info and media_info.strip() else None,
        )
        db.add(torrent)
        db.flush()

        for parsed_file in parsed.files:
            db.add(
                TorrentFile(
                    torrent_id=torrent.id,
                    file_path=parsed_file.file_path,
                    file_size_bytes=parsed_file.file_size_bytes,
                )
            )

        db.add(TrackerTorrentStatsCache(torrent_id=torrent.id))
        db.commit()
        db.refresh(torrent)
        return torrent, parsed
    except Exception:
        db.rollback()
        saved_path.unlink(missing_ok=True)
        raise
