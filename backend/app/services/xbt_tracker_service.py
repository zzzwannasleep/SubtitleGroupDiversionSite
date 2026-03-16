from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.torrent import Torrent
from app.models.user import User, UserStatus


class XbtTrackerError(ValueError):
    """Raised when XBT integration fails."""


def _normalize_mysql_dsn(dsn: str) -> str:
    if dsn.startswith("mysql://"):
        return f"mysql+pymysql://{dsn.removeprefix('mysql://')}"
    return dsn


@lru_cache
def _get_xbt_engine() -> Engine:
    settings = get_settings()
    if not settings.xbt_tracker_db_dsn:
        raise XbtTrackerError("XBT tracker database DSN is not configured")
    return create_engine(_normalize_mysql_dsn(settings.xbt_tracker_db_dsn), future=True, pool_pre_ping=True)


def _require_xbt_enabled() -> None:
    settings = get_settings()
    if settings.tracker_impl.strip().lower() != "xbt":
        raise XbtTrackerError("Current tracker implementation is not XBT")
    if not settings.xbt_tracker_db_dsn:
        raise XbtTrackerError("XBT tracker database DSN is not configured")


def _validate_tracker_credential(credential: str) -> None:
    if len(credential) != 32:
        raise XbtTrackerError("XBT requires 32-character tracker credentials")


def _can_leech(user: User) -> int:
    return 1 if user.status == UserStatus.ACTIVE else 0


def upsert_xbt_user(user: User) -> None:
    _require_xbt_enabled()
    _validate_tracker_credential(user.tracker_credential)

    try:
        with _get_xbt_engine().begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO xbt_users (uid, can_leech, wait_time, peers_limit, torrent_pass, downloaded, uploaded)
                    VALUES (:uid, :can_leech, 0, 0, :torrent_pass, 0, 0)
                    ON DUPLICATE KEY UPDATE
                        can_leech = VALUES(can_leech),
                        torrent_pass = VALUES(torrent_pass)
                    """
                ),
                {
                    "uid": user.id,
                    "can_leech": _can_leech(user),
                    "torrent_pass": user.tracker_credential,
                },
            )
    except Exception as exc:
        raise XbtTrackerError(f"Could not upsert XBT user {user.id}: {exc}") from exc


def delete_xbt_user(user_id: int) -> None:
    settings = get_settings()
    if settings.tracker_impl.strip().lower() != "xbt" or not settings.xbt_tracker_db_dsn:
        return

    try:
        with _get_xbt_engine().begin() as connection:
            connection.execute(text("DELETE FROM xbt_users WHERE uid = :uid"), {"uid": user_id})
    except Exception as exc:
        raise XbtTrackerError(f"Could not delete XBT user {user_id}: {exc}") from exc


def upsert_xbt_torrent(info_hash: str) -> None:
    _require_xbt_enabled()
    info_hash = info_hash.strip().lower()
    if len(info_hash) != 40:
        raise XbtTrackerError("XBT info_hash must be a 40-character hex string")

    try:
        with _get_xbt_engine().begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO xbt_torrents (info_hash, completed, leechers, seeders, flags, mtime, ctime)
                    VALUES (UNHEX(:info_hash), 0, 0, 0, 0, UNIX_TIMESTAMP(), UNIX_TIMESTAMP())
                    ON DUPLICATE KEY UPDATE
                        flags = 0,
                        mtime = VALUES(mtime)
                    """
                ),
                {"info_hash": info_hash},
            )
    except Exception as exc:
        raise XbtTrackerError(f"Could not upsert XBT torrent {info_hash}: {exc}") from exc


def delete_xbt_torrent(info_hash: str) -> None:
    settings = get_settings()
    if settings.tracker_impl.strip().lower() != "xbt" or not settings.xbt_tracker_db_dsn:
        return

    try:
        with _get_xbt_engine().begin() as connection:
            connection.execute(text("DELETE FROM xbt_torrents WHERE info_hash = UNHEX(:info_hash)"), {"info_hash": info_hash})
    except Exception as exc:
        raise XbtTrackerError(f"Could not delete XBT torrent {info_hash}: {exc}") from exc


def fetch_xbt_user_stats() -> list[dict[str, object]]:
    _require_xbt_enabled()

    try:
        with _get_xbt_engine().connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        torrent_pass AS tracker_credential,
                        uploaded AS uploaded_bytes,
                        downloaded AS downloaded_bytes
                    FROM xbt_users
                    """
                )
            ).mappings()
            return [dict(row) for row in rows]
    except Exception as exc:
        raise XbtTrackerError(f"Could not fetch XBT user stats: {exc}") from exc


def fetch_xbt_torrent_stats() -> list[dict[str, object]]:
    _require_xbt_enabled()

    try:
        with _get_xbt_engine().connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        LOWER(HEX(info_hash)) AS info_hash,
                        seeders,
                        leechers,
                        completed AS snatches,
                        completed AS finished
                    FROM xbt_torrents
                    """
                )
            ).mappings()
            return [dict(row) for row in rows]
    except Exception as exc:
        raise XbtTrackerError(f"Could not fetch XBT torrent stats: {exc}") from exc


def provision_xbt_state(db: Session) -> dict[str, int]:
    _require_xbt_enabled()

    users = db.scalars(select(User).order_by(User.id)).all()
    torrents = db.scalars(select(Torrent).order_by(Torrent.id)).all()

    for user in users:
        upsert_xbt_user(user)
    for torrent in torrents:
        upsert_xbt_torrent(torrent.info_hash)

    return {"users": len(users), "torrents": len(torrents)}
