from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.download_log import DownloadLog
from app.models.torrent import Torrent
from app.models.user import User
from app.services.torrent_parse_service import TorrentParseError, bencode_encode, decode_torrent_document


class TorrentDownloadError(ValueError):
    """Raised when a torrent cannot be downloaded or rewritten."""


def build_announce_url(tracker_credential: str) -> str:
    settings = get_settings()
    base_url = settings.tracker_base_url.rstrip("/")
    mode = settings.tracker_credential_mode.lower()
    encoded_credential = quote(tracker_credential, safe="")

    if mode == "xbt_path":
        parsed = urlsplit(base_url)
        path = parsed.path or "/announce"
        prefix, _, last_segment = path.rpartition("/")
        if not last_segment:
            raise TorrentDownloadError("TRACKER_BASE_URL must include an announce-like path when using xbt_path mode")
        rewritten_path = f"{prefix}/{encoded_credential}/{last_segment}" if prefix else f"/{encoded_credential}/{last_segment}"
        return urlunsplit((parsed.scheme, parsed.netloc, rewritten_path, parsed.query, parsed.fragment))

    if mode == "path":
        return f"{base_url}/{encoded_credential}"

    separator = "&" if "?" in base_url else "?"
    query_key = quote(settings.tracker_credential_query_key, safe="")
    return f"{base_url}{separator}{query_key}={encoded_credential}"


def rewrite_torrent_bytes(original_bytes: bytes, announce_url: str) -> bytes:
    try:
        document = decode_torrent_document(original_bytes)
    except TorrentParseError as exc:
        raise TorrentDownloadError(str(exc)) from exc

    announce_bytes = announce_url.encode("utf-8")
    document[b"announce"] = announce_bytes
    document[b"announce-list"] = [[announce_bytes]]
    return bencode_encode(document)


def create_download_payload(db: Session, *, torrent_id: int, user: User, requester_ip: str) -> tuple[bytes, Torrent]:
    torrent = db.scalar(select(Torrent).where(Torrent.id == torrent_id, Torrent.is_visible.is_(True)))
    if torrent is None:
        raise TorrentDownloadError("Torrent not found")

    torrent_path = Path(torrent.torrent_path)
    if not torrent_path.exists():
        raise TorrentDownloadError("Original torrent file is missing from storage")

    original_bytes = torrent_path.read_bytes()
    rewritten_bytes = rewrite_torrent_bytes(original_bytes, build_announce_url(user.tracker_credential))

    db.add(DownloadLog(torrent_id=torrent.id, user_id=user.id, ip=requester_ip))
    db.commit()
    return rewritten_bytes, torrent
