from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import quote, quote_from_bytes, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from torf import Torrent, _flatbencode as flatbencode

from apps.common.exceptions import BusinessException
from apps.releases.models import ReleaseStatus
from apps.tracker.models import TrackerTorrentSync


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TorrustAuthKey:
    key: str
    valid_until: datetime | None


@dataclass(slots=True)
class TrackerScrapeStats:
    seeders: int
    leechers: int
    completed: int


@dataclass(slots=True)
class TrackerApiStats:
    torrents: int
    seeders: int
    leechers: int
    completed: int
    announces_handled: int
    scrapes_handled: int


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

        valid_until = self._parse_valid_until(payload)
        if valid_until is None and duration_seconds > 0:
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

    def get_stats(self) -> TrackerApiStats:
        payload = self._request_json(
            method="GET",
            path=getattr(settings, "TORRUST_API_STATS_PATH", "/api/v1/stats"),
        )
        if not payload:
            return TrackerApiStats(
                torrents=0,
                seeders=0,
                leechers=0,
                completed=0,
                announces_handled=0,
                scrapes_handled=0,
            )

        announces_handled = sum(
            self._coerce_int(value) for key, value in payload.items() if str(key).endswith("announces_handled")
        )
        scrapes_handled = sum(
            self._coerce_int(value) for key, value in payload.items() if str(key).endswith("scrapes_handled")
        )
        return TrackerApiStats(
            torrents=self._coerce_int(payload.get("torrents")),
            seeders=self._coerce_int(payload.get("seeders")),
            leechers=self._coerce_int(payload.get("leechers")),
            completed=self._coerce_int(payload.get("completed")),
            announces_handled=announces_handled,
            scrapes_handled=scrapes_handled,
        )

    def scrape_infohash(self, *, infohash: str, auth_key: str = "") -> TrackerScrapeStats:
        try:
            infohash_bytes = bytes.fromhex(infohash)
        except ValueError as exc:
            raise BusinessException("Infohash 格式无效，无法执行 scrape。") from exc

        scrape_url = TrackerService.build_scrape_url(auth_key)
        separator = "&" if "?" in scrape_url else "?"
        query = f"info_hash={quote_from_bytes(infohash_bytes, safe='')}"
        request = Request(f"{scrape_url}{separator}{query}", method="GET")
        request.add_header("Accept", "application/octet-stream, text/plain, */*")
        body = self._perform_request(request, expect_json=False)
        return self._parse_scrape_response(body=body, infohash_bytes=infohash_bytes)

    def _request_json(self, *, method: str, path: str, allow_empty: bool = False) -> dict:
        query = urlencode({"token": self.token})
        url = f"{self.base_url}{path}"
        separator = "&" if "?" in url else "?"
        request = Request(f"{url}{separator}{query}", method=method)
        request.add_header("Accept", "application/json")
        body = self._perform_request(request, expect_json=True)
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

    def _perform_request(self, request: Request, *, expect_json: bool) -> bytes:
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            if expect_json:
                raise BusinessException(f"Torrust API 请求失败：HTTP {exc.code} {detail}".strip()) from exc
            raise BusinessException(f"Tracker scrape 请求失败：HTTP {exc.code} {detail}".strip()) from exc
        except URLError as exc:
            if expect_json:
                raise BusinessException("无法连接到 Torrust 管理 API。") from exc
            raise BusinessException("无法连接到 Tracker scrape 地址。") from exc

    @staticmethod
    def _coerce_int(value) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_valid_until(payload: dict) -> datetime | None:
        raw_value = payload.get("expires_at") or payload.get("expiry_time") or payload.get("valid_until")
        if raw_value in (None, ""):
            return None

        valid_until: datetime | None = None
        if isinstance(raw_value, (int, float)):
            valid_until = datetime.fromtimestamp(raw_value, tz=UTC)
        elif isinstance(raw_value, str):
            candidate = raw_value.strip()
            if not candidate:
                return None
            normalized_candidate = candidate.replace(" UTC", "+00:00").replace("Z", "+00:00")
            try:
                valid_until = datetime.fromisoformat(normalized_candidate)
            except ValueError:
                return None

        if valid_until is None:
            return None
        if timezone.is_naive(valid_until):
            return valid_until.replace(tzinfo=UTC)
        return valid_until

    @staticmethod
    def _parse_scrape_response(*, body: bytes, infohash_bytes: bytes) -> TrackerScrapeStats:
        try:
            payload = flatbencode.decode(body)
        except Exception as exc:  # pragma: no cover - flatbencode raises several internal exception types
            raise BusinessException("Tracker scrape 返回了无法解析的响应。") from exc

        if not isinstance(payload, dict):
            raise BusinessException("Tracker scrape 返回了意外的数据格式。")

        failure_reason = payload.get(b"failure reason") or payload.get("failure reason")
        if failure_reason:
            if isinstance(failure_reason, bytes):
                failure_reason = failure_reason.decode("utf-8", errors="ignore")
            raise BusinessException(f"Tracker scrape 失败：{failure_reason}")

        files = payload.get(b"files") or payload.get("files") or {}
        if not isinstance(files, dict):
            raise BusinessException("Tracker scrape 响应缺少 files 字段。")

        stats = files.get(infohash_bytes) or files.get(infohash_bytes.decode("latin1"))
        if not isinstance(stats, dict):
            return TrackerScrapeStats(seeders=0, leechers=0, completed=0)

        return TrackerScrapeStats(
            seeders=TorrustClient._coerce_int(stats.get(b"complete") or stats.get("complete")),
            leechers=TorrustClient._coerce_int(stats.get(b"incomplete") or stats.get("incomplete")),
            completed=TorrustClient._coerce_int(stats.get(b"downloaded") or stats.get("downloaded")),
        )


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
        if TrackerService.force_private_torrents():
            torrent.private = True
        torrent.trackers = [[announce_url]]
        return torrent.dump(validate=False)

    @staticmethod
    def get_announce_url_for_user(user) -> str:
        if not TrackerService.is_enabled():
            raise BusinessException("Tracker 尚未启用。")
        return TrackerService.build_announce_url(TrackerService._resolve_auth_key_for_user(user))

    @staticmethod
    def get_scrape_url_for_user(user) -> str:
        if not TrackerService.is_enabled():
            raise BusinessException("Tracker 尚未启用。")
        return TrackerService.build_scrape_url(TrackerService._resolve_auth_key_for_user(user))

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
        return TrackerService._build_tracker_url(announce_url, auth_key)

    @staticmethod
    def build_scrape_url(auth_key: str) -> str:
        scrape_url = (getattr(settings, "TRACKER_SCRAPE_URL", "") or "").strip()
        if not scrape_url:
            scrape_url = TrackerService._derive_scrape_base_url()
        return TrackerService._build_tracker_url(scrape_url, auth_key)

    @staticmethod
    def get_scrape_auth_key(preferred_user=None) -> str:
        shared_key = (getattr(settings, "TORRUST_SHARED_AUTH_KEY", "") or "").strip()
        if shared_key:
            return shared_key

        if TrackerService.auth_mode() == "shared":
            raise BusinessException("Torrust 共享鉴权 key 尚未配置。")

        from apps.users.models import User

        candidate = preferred_user
        if candidate is None or getattr(candidate, "status", None) != "active":
            candidate = User.objects.filter(status="active").order_by("id").first()
        if candidate is None:
            raise BusinessException("当前没有可用于 scrape 的激活用户。")
        return TrackerService.ensure_user_key(candidate)

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

    @staticmethod
    def _resolve_auth_key_for_user(user) -> str:
        mode = TrackerService.auth_mode()
        if mode == "shared":
            shared_key = (getattr(settings, "TORRUST_SHARED_AUTH_KEY", "") or "").strip()
            if not shared_key:
                raise BusinessException("Torrust 共享鉴权 key 尚未配置。")
            return shared_key
        return TrackerService.ensure_user_key(user)

    @staticmethod
    def _build_tracker_url(base_url: str, auth_key: str) -> str:
        parsed = urlsplit(base_url)
        path = parsed.path.rstrip("/")
        if auth_key:
            path = f"{path}/{quote(auth_key, safe='')}"
        return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))

    @staticmethod
    def _derive_scrape_base_url() -> str:
        announce_url = (getattr(settings, "TRACKER_ANNOUNCE_URL", "") or "").strip()
        if not announce_url:
            raise BusinessException("Tracker scrape 地址尚未配置。")

        parsed = urlsplit(announce_url)
        path = parsed.path.rstrip("/")
        if path.endswith("/announce"):
            path = f"{path[:-len('/announce')]}/scrape"
        else:
            path = f"{path}/scrape"
        return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))


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

    @staticmethod
    def sync_release_scrape_now(*, release) -> TrackerTorrentSync:
        sync, _ = TrackerTorrentSync.objects.get_or_create(
            release=release,
            defaults={"infohash": release.infohash},
        )
        sync.infohash = release.infohash
        sync.last_scrape_at = timezone.now()

        if not TrackerService.is_enabled() or release.status != ReleaseStatus.PUBLISHED:
            sync.last_error = ""
            sync.save(update_fields=["infohash", "last_scrape_at", "last_error"])
            return sync

        try:
            auth_key = TrackerService.get_scrape_auth_key(getattr(release, "created_by", None))
            stats = TorrustClient.from_settings().scrape_infohash(infohash=release.infohash, auth_key=auth_key)
            sync.last_scrape_seeders = stats.seeders
            sync.last_scrape_leechers = stats.leechers
            sync.last_scrape_completed = stats.completed
            sync.last_error = ""
            sync.save(
                update_fields=[
                    "infohash",
                    "last_scrape_at",
                    "last_scrape_seeders",
                    "last_scrape_leechers",
                    "last_scrape_completed",
                    "last_error",
                ]
            )
            type(release).objects.filter(pk=release.pk).update(
                active_peers=stats.seeders + stats.leechers,
                completion_count=stats.completed,
            )
        except BusinessException as exc:
            sync.last_error = str(exc)
            sync.save(update_fields=["infohash", "last_scrape_at", "last_error"])
            if getattr(settings, "TRACKER_SYNC_STRICT", False):
                raise
            logger.warning(
                "Failed to scrape tracker stats for release=%s infohash=%s",
                release.id,
                release.infohash,
                exc_info=True,
            )
        return sync


class TrackerAdminService:
    @staticmethod
    def get_overview() -> dict:
        from apps.releases.models import Release
        from apps.users.models import User

        tracker_stats = None
        tracker_message = ""
        tracker_reachable = False

        if TrackerService.is_enabled():
            try:
                tracker_stats = TorrustClient.from_settings().get_stats()
                tracker_reachable = True
            except BusinessException as exc:
                tracker_message = str(exc)

        scrape_base_url = ""
        if TrackerService.is_enabled():
            try:
                scrape_base_url = TrackerService.build_scrape_url("")
            except BusinessException as exc:
                tracker_message = str(exc)

        aggregates = TrackerTorrentSync.objects.aggregate(
            latest_sync_at=Max("last_synced_at"),
            latest_scrape_at=Max("last_scrape_at"),
        )
        return {
            "enabled": TrackerService.is_enabled(),
            "trackerReachable": tracker_reachable,
            "trackerMessage": tracker_message,
            "authMode": TrackerService.auth_mode(),
            "announceUrl": (getattr(settings, "TRACKER_ANNOUNCE_URL", "") or "").strip(),
            "scrapeUrl": scrape_base_url,
            "requireAuthDownloads": TrackerService.require_authenticated_downloads(),
            "forcePrivateTorrents": TrackerService.force_private_torrents(),
            "userCount": User.objects.count(),
            "activeUserCount": User.objects.filter(status="active").count(),
            "userKeysProvisioned": User.objects.exclude(tracker_passkey="").count(),
            "releaseSyncCount": TrackerTorrentSync.objects.count(),
            "publishedReleaseCount": Release.objects.filter(status=ReleaseStatus.PUBLISHED).count(),
            "whitelistedReleaseCount": TrackerTorrentSync.objects.filter(is_whitelisted=True).count(),
            "syncErrorCount": TrackerTorrentSync.objects.exclude(last_error="").count(),
            "latestSyncAt": aggregates["latest_sync_at"],
            "latestScrapeAt": aggregates["latest_scrape_at"],
            "trackerStats": None
            if tracker_stats is None
            else {
                "torrents": tracker_stats.torrents,
                "seeders": tracker_stats.seeders,
                "leechers": tracker_stats.leechers,
                "completed": tracker_stats.completed,
                "announcesHandled": tracker_stats.announces_handled,
                "scrapesHandled": tracker_stats.scrapes_handled,
            },
        }

    @staticmethod
    def sync(*, sync_users: bool, sync_releases: bool, sync_scrape: bool) -> dict:
        if not TrackerService.is_enabled():
            raise BusinessException("Tracker integration is not enabled.")

        if not any([sync_users, sync_releases, sync_scrape]):
            sync_users = True
            sync_releases = True
            sync_scrape = True

        from apps.releases.models import Release
        from apps.releases.services import ReleaseService
        from apps.users.models import User

        summary = {
            "usersProcessed": 0,
            "usersFailed": 0,
            "releasesProcessed": 0,
            "releasesFailed": 0,
            "scrapesProcessed": 0,
            "scrapesFailed": 0,
            "errors": [],
        }

        if sync_users:
            for user in User.objects.filter(status="active").order_by("id"):
                try:
                    TrackerService.ensure_user_key(user)
                    summary["usersProcessed"] += 1
                except BusinessException as exc:
                    summary["usersFailed"] += 1
                    summary["errors"].append(f"user:{user.id}:{exc}")
                    if getattr(settings, "TRACKER_SYNC_STRICT", False):
                        raise

        if sync_releases:
            for release in Release.objects.select_related("created_by").order_by("id"):
                try:
                    normalized_release = ReleaseService.normalize_existing_release_torrent(release)
                    TrackerSyncService.sync_release_now(release=normalized_release)
                    summary["releasesProcessed"] += 1
                except BusinessException as exc:
                    summary["releasesFailed"] += 1
                    summary["errors"].append(f"release:{release.id}:{exc}")
                    if getattr(settings, "TRACKER_SYNC_STRICT", False):
                        raise

        if sync_scrape:
            queryset = Release.objects.select_related("created_by").filter(status=ReleaseStatus.PUBLISHED).order_by("id")
            for release in queryset:
                try:
                    TrackerSyncService.sync_release_scrape_now(release=release)
                    summary["scrapesProcessed"] += 1
                except BusinessException as exc:
                    summary["scrapesFailed"] += 1
                    summary["errors"].append(f"scrape:{release.id}:{exc}")
                    if getattr(settings, "TRACKER_SYNC_STRICT", False):
                        raise

        return summary
