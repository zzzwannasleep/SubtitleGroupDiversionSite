from pathlib import Path

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

        if TrackerService.is_enabled():
            announce_url = TrackerService.get_announce_url_for_user(user)
            torrent_bytes = TrackerService.rewrite_download_torrent(
                torrent_bytes=torrent_bytes,
                announce_url=announce_url,
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
    def _extract_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
