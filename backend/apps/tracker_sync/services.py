import logging
import time

from django.conf import settings

from apps.tracker_sync.models import (
    TrackerSyncLog,
    TrackerSyncScope,
    TrackerSyncStatus,
    XbtFileMirror,
    XbtUserMirror,
)
from apps.users.models import User, UserStatus


logger = logging.getLogger("apps.tracker_sync")


class TrackerSyncService:
    @staticmethod
    def create_log(scope: str, target_name: str, status: str, message: str, user=None, release=None):
        return TrackerSyncLog.objects.create(
            scope=scope,
            target_name=target_name,
            status=status,
            message=message,
            user=user,
            release=release,
        )

    @classmethod
    def sync_user(cls, user: User):
        if not settings.XBT_SYNC_ENABLED:
            return cls.create_log(
                TrackerSyncScope.USER,
                user.username,
                TrackerSyncStatus.WARNING,
                "XBT 同步已关闭，跳过用户同步。",
                user=user,
            )

        try:
            XbtUserMirror.objects.update_or_create(
                uid=user.id,
                defaults={
                    "torrent_pass": user.passkey,
                    "can_leech": user.status == UserStatus.ACTIVE,
                },
            )
            return cls.create_log(
                TrackerSyncScope.USER,
                user.username,
                TrackerSyncStatus.SUCCESS,
                "用户状态与 passkey 已同步到 XBT。",
                user=user,
            )
        except Exception as exc:
            logger.exception("failed to sync tracker user %s", user.id)
            return cls.create_log(
                TrackerSyncScope.USER,
                user.username,
                TrackerSyncStatus.FAILED,
                f"同步用户到 XBT 失败：{exc}",
                user=user,
            )

    @classmethod
    def sync_release(cls, release):
        if not settings.XBT_SYNC_ENABLED:
            return cls.create_log(
                TrackerSyncScope.RELEASE,
                release.title,
                TrackerSyncStatus.WARNING,
                "XBT 同步已关闭，跳过资源同步。",
                release=release,
            )

        try:
            now = int(time.time())
            record, created = XbtFileMirror.objects.get_or_create(
                info_hash=bytes.fromhex(release.infohash),
                defaults={"ctime": now, "mtime": now},
            )
            record.flags = 0 if release.status == "published" else 1
            record.mtime = now
            if created:
                record.ctime = now
            record.save(update_fields=["flags", "mtime", "ctime"])
            return cls.create_log(
                TrackerSyncScope.RELEASE,
                release.title,
                TrackerSyncStatus.SUCCESS,
                "资源白名单状态已同步到 XBT。",
                release=release,
            )
        except Exception as exc:
            logger.exception("failed to sync tracker release %s", release.id)
            return cls.create_log(
                TrackerSyncScope.RELEASE,
                release.title,
                TrackerSyncStatus.FAILED,
                f"同步资源到 XBT 失败：{exc}",
                release=release,
            )

    @classmethod
    def sync_all(cls):
        user_failures = 0
        release_failures = 0
        warnings = 0
        for user in User.objects.all():
            log = cls.sync_user(user)
            if log.status == TrackerSyncStatus.FAILED:
                user_failures += 1
            elif log.status == TrackerSyncStatus.WARNING:
                warnings += 1
        from apps.releases.models import Release

        for release in Release.objects.all():
            log = cls.sync_release(release)
            if log.status == TrackerSyncStatus.FAILED:
                release_failures += 1
            elif log.status == TrackerSyncStatus.WARNING:
                warnings += 1

        if user_failures or release_failures:
            return cls.create_log(
                TrackerSyncScope.FULL,
                "全量同步",
                TrackerSyncStatus.FAILED,
                f"全量同步完成，但用户失败 {user_failures} 条、资源失败 {release_failures} 条。",
            )
        if warnings:
            return cls.create_log(
                TrackerSyncScope.FULL,
                "全量同步",
                TrackerSyncStatus.WARNING,
                f"全量同步完成，但有 {warnings} 条记录被跳过或仅记录警告。",
            )
        return cls.create_log(
            TrackerSyncScope.FULL,
            "全量同步",
            TrackerSyncStatus.SUCCESS,
            "用户状态和资源白名单已全量同步到 XBT。",
        )
