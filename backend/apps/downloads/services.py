from pathlib import Path

from django.db.models import F
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from apps.downloads.models import DownloadLog
from apps.users.models import User, UserStatus


class DownloadService:
    @staticmethod
    def resolve_user(request):
        user = request.user
        if getattr(user, "is_authenticated", False):
            if getattr(user, "status", None) != UserStatus.ACTIVE:
                raise PermissionDenied("当前账户已被禁用。")
            return user

        passkey = request.query_params.get("passkey")
        if not passkey:
            raise NotAuthenticated("请先登录或提供 passkey。")
        resolved_user = User.objects.filter(passkey=passkey, status=UserStatus.ACTIVE).first()
        if not resolved_user:
            raise PermissionDenied("passkey 无效或账户已被禁用。")
        return resolved_user

    @classmethod
    def build_download_torrent(cls, *, user, release, request):
        if release.status != "published":
            raise PermissionDenied("当前资源不可下载。")
        with release.torrent_file.open("rb") as torrent_handle:
            torrent_bytes = torrent_handle.read()
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
