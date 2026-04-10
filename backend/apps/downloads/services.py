from pathlib import Path

from django.conf import settings
from django.db.models import F
from django.utils.text import slugify
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from apps.audit.services import AuditService
from apps.common.torrent import inject_announce, privatize_torrent
from apps.downloads.models import DownloadLog
from apps.users.models import User, UserStatus


class DownloadService:
    @staticmethod
    def build_announce_url(user) -> str:
        base = settings.TRACKER_ANNOUNCE_BASE_URL.rstrip("/")
        return f"{base}/{user.passkey}/announce"

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
    def build_personalized_torrent(cls, *, user, release, request):
        if release.status != "published":
            raise PermissionDenied("当前资源不可下载。")
        with release.torrent_file.open("rb") as torrent_handle:
            personalized = inject_announce(torrent_handle.read(), cls.build_announce_url(user))
        DownloadLog.objects.create(
            user=user,
            release=release,
            ip_address=cls._extract_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        type(release).objects.filter(pk=release.pk).update(download_count=F("download_count") + 1)
        filename = slugify(release.title) or f"release-{release.pk}"
        return personalized, f"{filename}.torrent"

    @classmethod
    def build_private_torrent_from_upload(cls, *, user, torrent_file):
        original_name = Path(getattr(torrent_file, "name", "") or "uploaded.torrent")
        rewritten, metadata = privatize_torrent(torrent_file.read(), cls.build_announce_url(user))
        filename = slugify(metadata.name) or slugify(original_name.stem) or f"private-{metadata.infohash[:12]}"
        AuditService.log(
            user,
            "私有化 torrent",
            "torrent 工具",
            metadata.name,
            detail="上传 torrent 并注入个人 tracker。",
            payload={"infohash": metadata.infohash},
        )
        return rewritten, f"{filename}.torrent"

    @staticmethod
    def _extract_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
