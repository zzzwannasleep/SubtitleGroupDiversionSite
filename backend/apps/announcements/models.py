from django.db import models


class AnnouncementStatus(models.TextChoices):
    ONLINE = "online", "上线"
    DRAFT = "draft", "草稿"
    OFFLINE = "offline", "下线"


class AnnouncementAudience(models.TextChoices):
    ALL = "all", "全部"
    UPLOADER = "uploader", "上传者"
    ADMIN = "admin", "管理员"


DEFAULT_LOGIN_BACKGROUND_CSS = (
    "radial-gradient(circle at top left, rgba(96, 165, 250, 0.38), transparent 34%), "
    "radial-gradient(circle at 85% 15%, rgba(244, 114, 182, 0.28), transparent 30%), "
    "linear-gradient(135deg, #020617 0%, #0f172a 46%, #111827 100%)"
)


class LoginBackgroundType(models.TextChoices):
    API = "api", "API"
    FILE = "file", "文件"
    CSS = "css", "CSS"


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
    site_icon_url = models.URLField(blank=True)
    site_icon_file = models.FileField(upload_to="site/branding/", blank=True)
    login_background_type = models.CharField(
        max_length=20,
        choices=LoginBackgroundType.choices,
        default=LoginBackgroundType.CSS,
    )
    login_background_api_url = models.URLField(blank=True)
    login_background_file = models.FileField(upload_to="site/login-backgrounds/", blank=True)
    login_background_css = models.TextField(blank=True, default=DEFAULT_LOGIN_BACKGROUND_CSS)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "site_settings"
        verbose_name = "站点设置"
        verbose_name_plural = "站点设置"

    @classmethod
    def get_current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
