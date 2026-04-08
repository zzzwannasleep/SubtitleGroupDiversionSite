from django.db import models


class AnnouncementStatus(models.TextChoices):
    ONLINE = "online", "上线"
    DRAFT = "draft", "草稿"
    OFFLINE = "offline", "下线"


class AnnouncementAudience(models.TextChoices):
    ALL = "all", "全部"
    UPLOADER = "uploader", "上传者"
    ADMIN = "admin", "管理员"


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=AnnouncementStatus.choices, default=AnnouncementStatus.DRAFT)
    audience = models.CharField(max_length=20, choices=AnnouncementAudience.choices, default=AnnouncementAudience.ALL)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "announcements"
        ordering = ["-updated_at", "-id"]

    def __str__(self) -> str:
        return self.title


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=120, default="字幕组分流站")
    site_description = models.CharField(max_length=255, default="内部资源浏览、下载与 RSS 订阅入口")
    login_notice = models.TextField(blank=True)
    rss_base_path = models.CharField(max_length=255, default="/rss")
    download_notice = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "site_settings"
        verbose_name = "站点设置"
        verbose_name_plural = "站点设置"

    @classmethod
    def get_current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
