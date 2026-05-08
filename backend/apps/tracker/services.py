from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from torf import Torrent

from apps.common.exceptions import BusinessException
from apps.releases.models import ReleaseStatus
from apps.tracker.models import TrackerTorrentSync


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TorrustAuthKey:
    key: str
    valid_until: timezone.datetime | None


class TorrustClient:
    def __init__(self, *, base_url: str, token: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> "TorrustClient":
        base_url = (getattr(settings, "TORRUST_API_URL", "") or "").strip()
        token = (getattr(settings, "TORRUST_API_TOKEN", "") or "").strip()
        if not base_url or not token:
            raise BusinessException("Torrust 管理 API 尚未配置完成。")
        return cls(
            base_url=base_url,
            token=token,
            timeout=float(getattr(settings, "TORRUST_API_TIMEOUT_SECONDS", 5)),
        )

    def create_auth_key(self, *, duration_seconds: int) -> TorrustAuthKey:
        payload = self._request_json(
            method="POST",
            path=getattr(settings, "TORRUST_API_CREATE_KEY_PATH_TEMPLATE", "/api/v1/key/{duration_in_seconds}").format(
                duration_in_seconds=duration_seconds
            ),
        )
        key = str(payload.get("key") or payload.get("auth_key") or payload.get("token") or "").strip()
        if not key:
            raise BusinessException("Torrust 未返回可用的 tracker key。")

        expires_at_value = payload.get("expires_at") or payload.get("valid_until")
        valid_until = None
        if isinstance(expires_at_value, str) and expires_at_value.strip():
            valid_until = timezone.datetime.fromisoformat(expires_at_value.replace("Z", "+00:00"))
        elif duration_seconds > 0:
            valid_until = timezone.now() + timedelta(seconds=duration_seconds)
        return TorrustAuthKey(key=key, valid_until=valid_until)

    def whitelist_infohash(self, infohash: str) -> None:
        path = getattr(settings, "TORRUST_API_WHITELIST_PATH_TEMPLATE", "/api/v1/whitelist/{infohash}").format(
            infohash=infohash
        )
        self._request_json(method="POST", path=path, allow_empty=True)

    def remove_infohash(self, infohash: str) -> None:
        path = getattr(settings, "TORRUST_API_WHITELIST_PATH_TEMPLATE", "/api/v1/whitelist/{infohash}").format(
            infohash=infohash
        )
        self._request_json(method="DELETE", path=path, allow_empty=True)

    def _request_json(self, *, method: str, path: str, allow_empty: bool = False) -> dict:
        query = urlencode({"token": self.token})
        url = f"{self.base_url}{path}"
        separator = "&" if "?" in url else "?"
        request = Request(f"{url}{separator}{query}", method=method)
        request.add_header("Accept", "application/json")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise BusinessException(f"Torrust API 请求失败：HTTP {exc.code} {detail}".strip()) from exc
        except URLError as exc:
            raise BusinessException("无法连接到 Torrust 管理 API。") from exc

        if not body:
            return {}

        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            if allow_empty:
                return {}
            raise BusinessException("Torrust API 返回了无法解析的响应。") from exc

        if isinstance(data, dict):
            return data
        if allow_empty:
            return {}
        raise BusinessException("Torrust API 返回了意外的数据格式。")


class TrackerService:
    @staticmethod
    def is_enabled() -> bool:
        return bool(getattr(settings, "TRACKER_ENABLED", False))

    @staticmethod
    def force_private_torrents() -> bool:
        return TrackerService.is_enabled() and bool(getattr(settings, "TRACKER_FORCE_PRIVATE_TORRENTS", True))

    @staticmethod
    def require_authenticated_downloads() -> bool:
        return TrackerService.is_enabled() and bool(getattr(settings, "TRACKER_REQUIRE_AUTH_DOWNLOADS", True))

    @staticmethod
    def auth_mode() -> str:
        return getattr(settings, "TRACKER_AUTH_MODE", "per_user")

    @staticmethod
    def normalize_uploaded_torrent(torrent_bytes: bytes) -> bytes:
        if not TrackerService.force_private_torrents():
            return torrent_bytes

        torrent = Torrent.read_stream(torrent_bytes, validate=False)
        if torrent.private:
            return torrent_bytes

        torrent.private = True
        return torrent.dump(validate=False)

    @staticmethod
    def rewrite_download_torrent(*, torrent_bytes: bytes, announce_url: str) -> bytes:
        torrent = Torrent.read_stream(torrent_bytes, validate=False)
        torrent.trackers = [[announce_url]]
        return torrent.dump(validate=False)

    @staticmethod
    def get_announce_url_for_user(user) -> str:
        if not TrackerService.is_enabled():
            raise BusinessException("Tracker 尚未启用。")

        mode = TrackerService.auth_mode()
        if mode == "shared":
            shared_key = (getattr(settings, "TORRUST_SHARED_AUTH_KEY", "") or "").strip()
            if not shared_key:
                raise BusinessException("Torrust 共享鉴权 key 尚未配置。")
            return TrackerService.build_announce_url(shared_key)

        key = TrackerService.ensure_user_key(user)
        return TrackerService.build_announce_url(key)

    @staticmethod
    def ensure_user_key(user) -> str:
        renewal_window = int(getattr(settings, "TORRUST_KEY_RENEWAL_WINDOW_SECONDS", 86400))
        valid_until = getattr(user, "tracker_key_valid_until", None)
        passkey = (getattr(user, "tracker_passkey", "") or "").strip()

        if passkey and (valid_until is None or valid_until > timezone.now() + timedelta(seconds=renewal_window)):
            return passkey

        duration_seconds = int(getattr(settings, "TORRUST_KEY_TTL_SECONDS", 315360000))
        auth_key = TorrustClient.from_settings().create_auth_key(duration_seconds=duration_seconds)
        user.tracker_passkey = auth_key.key
        user.tracker_key_valid_until = auth_key.valid_until
        user.save(update_fields=["tracker_passkey", "tracker_key_valid_until"])
        return auth_key.key

    @staticmethod
    def build_announce_url(auth_key: str) -> str:
        announce_url = (getattr(settings, "TRACKER_ANNOUNCE_URL", "") or "").strip()
        if not announce_url:
            raise BusinessException("Tracker announce 地址尚未配置。")

        parsed = urlsplit(announce_url)
        path = parsed.path.rstrip("/")
        if auth_key:
            path = f"{path}/{quote(auth_key, safe='')}"
        return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))

    @staticmethod
    def schedule_user_key_provision(user) -> None:
        if not TrackerService.is_enabled() or TrackerService.auth_mode() != "per_user":
            return
        if getattr(user, "status", None) != "active":
            return

        user_id = user.id

        def _provision() -> None:
            from apps.users.models import User

            tracked_user = User.objects.filter(pk=user_id).first()
            if tracked_user is None:
                return
            try:
                TrackerService.ensure_user_key(tracked_user)
            except BusinessException:
                if getattr(settings, "TRACKER_SYNC_STRICT", False):
                    raise
                logger.warning("Failed to provision tracker key for user=%s", user_id, exc_info=True)

        transaction.on_commit(_provision)


class TrackerSyncService:
    @staticmethod
    def schedule_release_sync(*, release, previous_infohash: str | None = None, previous_status: str | None = None) -> None:
        release_id = release.id

        def _sync() -> None:
            from apps.releases.models import Release

            tracked_release = Release.objects.select_related("created_by").filter(pk=release_id).first()
            if tracked_release is None:
                return
            TrackerSyncService.sync_release_now(
                release=tracked_release,
                previous_infohash=previous_infohash,
                previous_status=previous_status,
            )

        transaction.on_commit(_sync)

    @staticmethod
    def sync_release_now(*, release, previous_infohash: str | None = None, previous_status: str | None = None) -> TrackerTorrentSync:
        sync, _ = TrackerTorrentSync.objects.get_or_create(
            release=release,
            defaults={"infohash": release.infohash},
        )
        sync.infohash = release.infohash
        sync.last_synced_at = timezone.now()

        if not TrackerService.is_enabled():
            sync.is_whitelisted = False
            sync.last_error = ""
            sync.save(update_fields=["infohash", "is_whitelisted", "last_synced_at", "last_error"])
            return sync

        should_whitelist = release.status == ReleaseStatus.PUBLISHED
        previous_status = previous_status or release.status
        previous_infohash = previous_infohash or release.infohash

        try:
            client = TorrustClient.from_settings()
            if previous_status == ReleaseStatus.PUBLISHED and (previous_infohash != release.infohash or not should_whitelist):
                client.remove_infohash(previous_infohash)
            if should_whitelist:
                client.whitelist_infohash(release.infohash)
            sync.is_whitelisted = should_whitelist
            sync.last_error = ""
        except BusinessException as exc:
            sync.last_error = str(exc)
            sync.save(update_fields=["infohash", "last_synced_at", "last_error"])
            if getattr(settings, "TRACKER_SYNC_STRICT", False):
                raise
            logger.warning(
                "Failed to synchronize torrent whitelist for release=%s infohash=%s",
                release.id,
                release.infohash,
                exc_info=True,
            )
            return sync

        sync.save(update_fields=["infohash", "is_whitelisted", "last_synced_at", "last_error"])
        return sync

