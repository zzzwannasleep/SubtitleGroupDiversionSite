from django.conf import settings
from django.db import models

from apps.releases.models import Release


class TrackerSyncScope(models.TextChoices):
    USER = "user", "用户"
    RELEASE = "release", "资源"
    FULL = "full", "全量"


class TrackerSyncStatus(models.TextChoices):
    SUCCESS = "success", "成功"
    WARNING = "warning", "警告"
    FAILED = "failed", "失败"


class TrackerSyncLog(models.Model):
    scope = models.CharField(max_length=20, choices=TrackerSyncScope.choices)
    target_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=TrackerSyncStatus.choices)
    message = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tracker_sync_logs",
    )
    release = models.ForeignKey(
        Release,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tracker_sync_logs",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tracker_sync_logs"
        ordering = ["-updated_at", "-id"]


class XbtUserMirror(models.Model):
    uid = models.PositiveBigIntegerField(primary_key=True)
    torrent_pass = models.CharField(max_length=32, unique=True)
    can_leech = models.BooleanField(default=True)
    downloaded = models.BigIntegerField(default=0)
    uploaded = models.BigIntegerField(default=0)
    completed = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "xbt_users"
        # XBT owns the real table schema. Django only maps and updates rows.
        managed = False


class XbtFileMirror(models.Model):
    info_hash = models.BinaryField(max_length=20, primary_key=True)
    leechers = models.PositiveIntegerField(default=0)
    seeders = models.PositiveIntegerField(default=0)
    completed = models.PositiveIntegerField(default=0)
    flags = models.PositiveIntegerField(default=0)
    mtime = models.PositiveIntegerField(default=0)
    ctime = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "xbt_files"
        # XBT owns the real table schema. Django only maps and updates rows.
        managed = False
