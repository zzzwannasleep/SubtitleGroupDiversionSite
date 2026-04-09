import logging
import time
from datetime import datetime, timezone as dt_timezone

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
    OVERVIEW_LOG_LIMIT = 20
    OVERVIEW_FAILED_LOG_LIMIT = 10
    DETAIL_LOG_LIMIT = 10

    @staticmethod
    def _xbt_database_alias() -> str:
        return settings.XBT_SYNC_DATABASE_ALIAS

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

    @staticmethod
    def _unix_to_iso(value: int | None) -> str | None:
        if not value:
            return None
        return datetime.fromtimestamp(value, tz=dt_timezone.utc).isoformat()

    @staticmethod
    def _serialize_log(log: TrackerSyncLog | None):
        if not log:
            return None
        return {
            "status": log.status,
            "message": log.message,
            "updatedAt": log.updated_at.isoformat(),
        }

    @classmethod
    def _recent_logs(cls, *, scope: str, user=None, release=None, limit: int | None = None):
        logs = TrackerSyncLog.objects.filter(scope=scope)
        if user is not None:
            logs = logs.filter(user=user)
        if release is not None:
            logs = logs.filter(release=release)
        return list(logs[: limit or cls.DETAIL_LOG_LIMIT])

    @classmethod
    def build_overview(cls):
        logs = TrackerSyncLog.objects.all()
        success_logs = logs.filter(status=TrackerSyncStatus.SUCCESS)
        warning_logs = logs.filter(status=TrackerSyncStatus.WARNING)
        failed_logs = logs.filter(status=TrackerSyncStatus.FAILED)
        last_full_log = logs.filter(scope=TrackerSyncScope.FULL).order_by("-updated_at", "-id").first()

        return {
            "summary": {
                "xbtSyncEnabled": settings.XBT_SYNC_ENABLED,
                "xbtDatabaseAlias": cls._xbt_database_alias(),
                "totalLogs": logs.count(),
                "successCount": success_logs.count(),
                "warningCount": warning_logs.count(),
                "failedCount": failed_logs.count(),
                "pendingCount": warning_logs.count() + failed_logs.count(),
                "lastSuccessAt": success_logs.values_list("updated_at", flat=True).first(),
                "lastFailureAt": failed_logs.values_list("updated_at", flat=True).first(),
                "lastFullSyncAt": last_full_log.updated_at if last_full_log else None,
            },
            "latestLogs": logs[: cls.OVERVIEW_LOG_LIMIT],
            "failedLogs": failed_logs[: cls.OVERVIEW_FAILED_LOG_LIMIT],
        }

    @classmethod
    def retry_log(cls, log: TrackerSyncLog):
        if log.scope == TrackerSyncScope.FULL:
            return cls.sync_all()
        if log.scope == TrackerSyncScope.USER:
            if log.user_id is None:
                return cls.create_log(
                    TrackerSyncScope.USER,
                    log.target_name,
                    TrackerSyncStatus.WARNING,
                    "原始同步记录缺少用户关联，无法重试。",
                )
            return cls.sync_user_by_id(log.user_id)
        if log.scope == TrackerSyncScope.RELEASE:
            if log.release_id is None:
                return cls.create_log(
                    TrackerSyncScope.RELEASE,
                    log.target_name,
                    TrackerSyncStatus.WARNING,
                    "原始同步记录缺少资源关联，无法重试。",
                )
            return cls.sync_release_by_id(log.release_id)
        return cls.create_log(
            log.scope,
            log.target_name,
            TrackerSyncStatus.WARNING,
            "不支持的同步范围，无法重试。",
        )

    @classmethod
    def get_user_sync_snapshot(cls, user: User):
        latest_log = TrackerSyncLog.objects.filter(scope=TrackerSyncScope.USER, user=user).order_by("-updated_at", "-id").first()
        xbt_state = {
            "state": "missing",
            "canLeech": None,
            "downloaded": None,
            "uploaded": None,
            "completed": None,
        }
        try:
            mirror = XbtUserMirror.objects.using(cls._xbt_database_alias()).filter(uid=user.id).first()
            if mirror:
                xbt_state = {
                    "state": "enabled" if mirror.can_leech else "disabled",
                    "canLeech": mirror.can_leech,
                    "downloaded": mirror.downloaded,
                    "uploaded": mirror.uploaded,
                    "completed": mirror.completed,
                }
        except Exception:
            logger.exception("failed to read xbt user mirror for %s via %s", user.id, cls._xbt_database_alias())
            xbt_state = {
                "state": "unavailable",
                "canLeech": None,
                "downloaded": None,
                "uploaded": None,
                "completed": None,
            }

        return {
            "trackerSync": cls._serialize_log(latest_log),
            "xbtUser": xbt_state,
        }

    @classmethod
    def build_user_detail(cls, user: User):
        snapshot = cls.get_user_sync_snapshot(user)
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "displayName": user.display_name,
                "role": user.role,
                "status": user.status,
                "passkey": user.passkey,
            },
            "trackerSync": snapshot["trackerSync"],
            "xbtUser": snapshot["xbtUser"],
            "recentLogs": cls._recent_logs(scope=TrackerSyncScope.USER, user=user),
        }

    @classmethod
    def get_release_sync_snapshot(cls, release):
        latest_log = (
            TrackerSyncLog.objects.filter(scope=TrackerSyncScope.RELEASE, release=release)
            .order_by("-updated_at", "-id")
            .first()
        )
        xbt_state = {
            "state": "missing",
            "seeders": None,
            "leechers": None,
            "completed": None,
            "createdAt": None,
            "updatedAt": None,
        }
        try:
            mirror = XbtFileMirror.objects.using(cls._xbt_database_alias()).filter(info_hash=bytes.fromhex(release.infohash)).first()
            if mirror:
                xbt_state = {
                    "state": "whitelisted" if mirror.flags == 0 else "deleted",
                    "seeders": mirror.seeders,
                    "leechers": mirror.leechers,
                    "completed": mirror.completed,
                    "createdAt": cls._unix_to_iso(mirror.ctime),
                    "updatedAt": cls._unix_to_iso(mirror.mtime),
                }
        except Exception:
            logger.exception("failed to read xbt file mirror for %s via %s", release.id, cls._xbt_database_alias())
            xbt_state = {
                "state": "unavailable",
                "seeders": None,
                "leechers": None,
                "completed": None,
                "createdAt": None,
                "updatedAt": None,
            }

        return {
            "trackerSync": cls._serialize_log(latest_log),
            "xbtFile": xbt_state,
        }

    @classmethod
    def build_release_detail(cls, release):
        snapshot = cls.get_release_sync_snapshot(release)
        return {
            "release": {
                "id": release.id,
                "title": release.title,
                "status": release.status,
                "infohash": release.infohash,
                "publishedAt": release.published_at or release.created_at,
                "createdById": release.created_by_id,
            },
            "trackerSync": snapshot["trackerSync"],
            "xbtFile": snapshot["xbtFile"],
            "recentLogs": cls._recent_logs(scope=TrackerSyncScope.RELEASE, release=release),
        }

    @classmethod
    def sync_user_by_id(cls, user_id: int):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return cls.create_log(
                TrackerSyncScope.USER,
                f"用户#{user_id}",
                TrackerSyncStatus.WARNING,
                "用户不存在，跳过 XBT 同步。",
            )
        return cls.sync_user(user)

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
            XbtUserMirror.objects.using(cls._xbt_database_alias()).update_or_create(
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
            logger.exception("failed to sync tracker user %s via %s", user.id, cls._xbt_database_alias())
            return cls.create_log(
                TrackerSyncScope.USER,
                user.username,
                TrackerSyncStatus.FAILED,
                f"同步用户到 XBT 失败：{exc}",
                user=user,
            )

    @classmethod
    def sync_release_by_id(cls, release_id: int):
        from apps.releases.models import Release

        release = Release.objects.filter(pk=release_id).first()
        if not release:
            return cls.create_log(
                TrackerSyncScope.RELEASE,
                f"资源#{release_id}",
                TrackerSyncStatus.WARNING,
                "资源不存在，跳过 XBT 同步。",
            )
        return cls.sync_release(release)

    @classmethod
    def sync_release(cls, release):
        from apps.releases.models import ReleaseStatus

        if not settings.XBT_SYNC_ENABLED:
            return cls.create_log(
                TrackerSyncScope.RELEASE,
                release.title,
                TrackerSyncStatus.WARNING,
                "XBT 同步已关闭，跳过资源同步。",
                release=release,
            )

        try:
            if not release.infohash:
                raise ValueError("资源缺少 infohash。")

            mirrors = XbtFileMirror.objects.using(cls._xbt_database_alias())
            info_hash = bytes.fromhex(release.infohash)
            now = int(time.time())
            if release.status == ReleaseStatus.PUBLISHED:
                record, created = mirrors.get_or_create(
                    info_hash=info_hash,
                    defaults={"ctime": now, "mtime": now},
                )
                update_fields = ["flags", "mtime"]
                record.flags = 0
                record.mtime = now
                if created or not record.ctime:
                    record.ctime = now
                    update_fields.append("ctime")
                record.save(update_fields=update_fields)
                return cls.create_log(
                    TrackerSyncScope.RELEASE,
                    release.title,
                    TrackerSyncStatus.SUCCESS,
                    "资源白名单状态已同步到 XBT。",
                    release=release,
                )

            updated = mirrors.filter(info_hash=info_hash).update(flags=1, mtime=now)
            message = (
                "资源已从 XBT 白名单中移除。"
                if updated
                else "资源当前未发布且不在 XBT 白名单中，跳过写入。"
            )
            return cls.create_log(
                TrackerSyncScope.RELEASE,
                release.title,
                TrackerSyncStatus.SUCCESS,
                message,
                release=release,
            )
        except Exception as exc:
            logger.exception("failed to sync tracker release %s via %s", release.id, cls._xbt_database_alias())
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
        for user in User.objects.order_by("id").iterator():
            log = cls.sync_user(user)
            if log.status == TrackerSyncStatus.FAILED:
                user_failures += 1
            elif log.status == TrackerSyncStatus.WARNING:
                warnings += 1
        from apps.releases.models import Release

        for release in Release.objects.order_by("id").iterator():
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
