from pathlib import Path, PurePosixPath
from urllib.parse import quote, urljoin

from django.conf import settings
from django.db.models import F
from rest_framework.exceptions import PermissionDenied

from apps.downloads.models import DownloadLog
from apps.tracker.services import TrackerService
from apps.users.models import UserStatus


class DownloadService:
    @staticmethod
    def resolve_user(request):
        user = request.user
        if getattr(user, "is_authenticated", False):
            if getattr(user, "status", None) != UserStatus.ACTIVE:
                raise PermissionDenied("当前账号已被禁用。")
            return user

        passkey = request.GET.get("passkey")
        if passkey:
            tracked_user = TrackerService.resolve_active_user_by_passkey(passkey)
            if tracked_user is None:
                raise PermissionDenied("RSS passkey 无效或账号已被禁用。")
            return tracked_user

        if TrackerService.require_authenticated_downloads():
            raise PermissionDenied("Private Tracker 已启用，请先登录后再下载种子。")
        return None

    @classmethod
    def build_download_torrent(cls, *, user, release, request):
        if release.status != "published":
            raise PermissionDenied("当前资源不可下载。")

        with release.torrent_file.open("rb") as torrent_handle:
            torrent_bytes = torrent_handle.read()

        webseed_root_url = cls._build_webseed_root_url(release=release, request=request)
        if TrackerService.is_enabled() or webseed_root_url:
            announce_url = TrackerService.get_announce_url_for_user(user) if TrackerService.is_enabled() else None
            torrent_bytes = TrackerService.rewrite_download_torrent(
                torrent_bytes=torrent_bytes,
                announce_url=announce_url,
                webseed_urls=[webseed_root_url] if webseed_root_url else None,
            )

        DownloadLog.objects.create(
            user=user,
            release=release,
            ip_address=cls._extract_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        type(release).objects.filter(pk=release.pk).update(download_count=F("download_count") + 1)

        filename = Path(release.torrent_file.name).name or f"release-{release.pk}.torrent"
        if not filename.lower().endswith(".torrent"):
            filename = f"{filename}.torrent"
        return torrent_bytes, filename

    @staticmethod
    def _normalize_public_path(value: str) -> str:
        normalized = (value or "/").strip() or "/"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        if not normalized.endswith("/"):
            normalized = f"{normalized}/"
        return normalized

    @classmethod
    def _build_public_base_url(cls, *, source_kind: str, request) -> str:
        if source_kind == "library":
            public_base = (getattr(settings, "WEBSEED_LIBRARY_PUBLIC_URL", "") or "").strip().rstrip("/")
            if public_base:
                return f"{public_base}/"
            return request.build_absolute_uri(cls._normalize_public_path(settings.WEBSEED_LIBRARY_URL_PATH))
        return request.build_absolute_uri(cls._normalize_public_path(settings.MEDIA_URL))

    @classmethod
    def _join_public_url(cls, *, base_url: str, relative_path: str = "", trailing_slash: bool = False) -> str:
        encoded_path = quote((relative_path or "").strip("/"), safe="/")
        if trailing_slash and encoded_path:
            encoded_path = f"{encoded_path}/"
        if trailing_slash and not encoded_path:
            return base_url.rstrip("/") + "/"
        if not encoded_path:
            return base_url
        return urljoin(base_url, encoded_path)

    @staticmethod
    def _resolve_webseed_source_kind(*, stored_path: str) -> str:
        candidate = str(stored_path or "").strip()
        if not candidate:
            return "managed"

        managed_path = Path(settings.MEDIA_ROOT).joinpath(*PurePosixPath(candidate).parts)
        library_root = Path(getattr(settings, "WEBSEED_LIBRARY_ROOT", settings.MEDIA_ROOT))
        library_path = library_root.joinpath(*PurePosixPath(candidate).parts)

        managed_exists = managed_path.exists()
        library_exists = library_path.exists()
        if library_exists and not managed_exists:
            return "library"
        return "managed"

    @classmethod
    def build_webseed_file_url(cls, *, stored_path: str, request) -> str:
        source_kind = cls._resolve_webseed_source_kind(stored_path=stored_path)
        base_url = cls._build_public_base_url(source_kind=source_kind, request=request)
        return cls._join_public_url(base_url=base_url, relative_path=stored_path)

    @classmethod
    def build_webseed_root_url_for_paths(cls, *, stored_paths: list[str], relative_paths: list[str], request) -> str | None:
        if not stored_paths or not relative_paths:
            return None

        first_stored_path = str(stored_paths[0] or "").strip()
        first_relative_path = str(relative_paths[0] or "").strip()
        stored_parts = list(PurePosixPath(first_stored_path).parts)
        relative_parts = list(PurePosixPath(first_relative_path).parts)
        strip_count = len(relative_parts) + (1 if len(stored_paths) > 1 else 0)
        root_parts = stored_parts[:-strip_count] if strip_count > 0 else stored_parts
        root_suffix = "/".join(root_parts).strip("/")
        source_kind = cls._resolve_webseed_source_kind(stored_path=first_stored_path)
        base_url = cls._build_public_base_url(source_kind=source_kind, request=request)
        return cls._join_public_url(base_url=base_url, relative_path=root_suffix, trailing_slash=True)

    @classmethod
    def _build_webseed_root_url(cls, *, release, request) -> str | None:
        webseed_files = list(release.webseed_files.all())
        if not webseed_files:
            return None
        return cls.build_webseed_root_url_for_paths(
            stored_paths=[str(item.storage_file.name) for item in webseed_files],
            relative_paths=[str(item.relative_path) for item in webseed_files],
            request=request,
        )

    @staticmethod
    def _extract_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
