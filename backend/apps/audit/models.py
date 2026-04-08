from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_name = models.CharField(max_length=120)
    action = models.CharField(max_length=120)
    target_type = models.CharField(max_length=120)
    target_name = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    payload_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.actor_name}:{self.action}"
