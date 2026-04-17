from django.conf import settings
from django.db import models

from apps.releases.models import Release


class DownloadLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="download_logs",
        null=True,
        blank=True,
    )
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="download_logs")
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "downloads"
        ordering = ["-downloaded_at", "-id"]

    def __str__(self) -> str:
        return f"{self.user_id or 'anonymous'}:{self.release_id}"
