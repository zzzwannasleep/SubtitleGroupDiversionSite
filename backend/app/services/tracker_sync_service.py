from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.torrent import Torrent
from app.models.tracker_torrent_stats_cache import TrackerTorrentStatsCache
from app.models.tracker_user_stats_cache import TrackerUserStatsCache
from app.models.user import User


class TrackerSyncError(ValueError):
    """Raised when tracker sync cannot be completed."""


def _source_name() -> str:
    tracker_impl = get_settings().tracker_impl.strip().lower()
    return tracker_impl or "tracker"


def _normalize_payload(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    raise TrackerSyncError("Tracker sync endpoint returned an unsupported payload shape")


def _to_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _to_decimal(value: object) -> Decimal | None:
    if value in (None, "", "null"):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _fetch_json(url: str) -> object:
    settings = get_settings()
    try:
        with httpx.Client(timeout=settings.tracker_sync_timeout_seconds) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise TrackerSyncError(f"Tracker sync request failed: {exc}") from exc


def _sync_user_stats(db: Session, items: Iterable[dict[str, object]]) -> int:
    updated = 0
    for item in items:
        credential = item.get("tracker_credential") or item.get("credential") or item.get("passkey")
        if not isinstance(credential, str) or not credential:
            continue

        user = db.scalar(select(User).where(User.tracker_credential == credential))
        if user is None:
            continue

        cache = db.get(TrackerUserStatsCache, user.id)
        if cache is None:
            cache = TrackerUserStatsCache(user_id=user.id)

        cache.uploaded_bytes = _to_int(item.get("uploaded_bytes", item.get("uploaded", 0)))
        cache.downloaded_bytes = _to_int(item.get("downloaded_bytes", item.get("downloaded", 0)))
        cache.ratio = _to_decimal(item.get("ratio"))
        cache.updated_at = datetime.now(UTC)
        cache.source = _source_name()
        db.add(cache)
        updated += 1

    return updated


def _sync_torrent_stats(db: Session, items: Iterable[dict[str, object]]) -> int:
    updated = 0
    for item in items:
        info_hash = item.get("info_hash")
        if not isinstance(info_hash, str) or not info_hash:
            continue

        torrent = db.scalar(select(Torrent).where(Torrent.info_hash == info_hash.lower()))
        if torrent is None:
            continue

        cache = db.get(TrackerTorrentStatsCache, torrent.id)
        if cache is None:
            cache = TrackerTorrentStatsCache(torrent_id=torrent.id)

        cache.seeders = _to_int(item.get("seeders"))
        cache.leechers = _to_int(item.get("leechers"))
        cache.snatches = _to_int(item.get("snatches"))
        cache.finished = _to_int(item.get("finished"))
        cache.updated_at = datetime.now(UTC)
        cache.source = _source_name()
        db.add(cache)
        updated += 1

    return updated


def sync_tracker_stats(db: Session) -> dict[str, object]:
    settings = get_settings()

    if settings.tracker_sync_mode != "pull":
        return {
            "user_stats_updated": 0,
            "torrent_stats_updated": 0,
            "skipped": True,
            "message": f"Tracker sync mode '{settings.tracker_sync_mode}' does not support manual pull sync",
        }

    if not settings.tracker_user_stats_endpoint and not settings.tracker_torrent_stats_endpoint:
        return {
            "user_stats_updated": 0,
            "torrent_stats_updated": 0,
            "skipped": True,
            "message": "Tracker sync endpoints are not configured",
        }

    user_updates = 0
    torrent_updates = 0

    if settings.tracker_user_stats_endpoint:
        user_payload = _normalize_payload(_fetch_json(settings.tracker_user_stats_endpoint))
        user_updates = _sync_user_stats(db, user_payload)

    if settings.tracker_torrent_stats_endpoint:
        torrent_payload = _normalize_payload(_fetch_json(settings.tracker_torrent_stats_endpoint))
        torrent_updates = _sync_torrent_stats(db, torrent_payload)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise TrackerSyncError(f"Tracker stats sync could not be committed: {exc}") from exc

    return {
        "user_stats_updated": user_updates,
        "torrent_stats_updated": torrent_updates,
        "skipped": False,
        "message": "Tracker stats sync completed",
    }
