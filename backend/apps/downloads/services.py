from pathlib import Path, PurePosixPath

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
    def _build_webseed_root_url(*, release, request) -> str | None:
        webseed_files = list(release.webseed_files.all())
        if not webseed_files:
            return None
        first_entry = webseed_files[0]
        stored_parts = list(PurePosixPath(first_entry.storage_file.name).parts)
        relative_parts = list(PurePosixPath(first_entry.relative_path).parts)
        strip_count = len(relative_parts) + (1 if len(webseed_files) > 1 else 0)
        root_parts = stored_parts[:-strip_count] if strip_count > 0 else stored_parts
        root_path = f"{settings.MEDIA_URL.rstrip('/')}/{'/'.join(root_parts).strip('/')}/"
        return request.build_absolute_uri(root_path)

    @staticmethod
    def _extract_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
