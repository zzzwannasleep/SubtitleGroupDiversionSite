import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.common.utils import generate_secret_token


INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
INVITE_CODE_LENGTH = 12


def compact_invite_code(value: str) -> str:
    return "".join(char for char in value.upper() if char.isalnum())


def normalize_invite_code(value: str) -> str:
    compact = compact_invite_code(value)
    return "-".join(compact[index : index + 4] for index in range(0, len(compact), 4))


def generate_invite_code() -> str:
    compact = "".join(secrets.choice(INVITE_CODE_ALPHABET) for _ in range(INVITE_CODE_LENGTH))
    return normalize_invite_code(compact)


class UserRole(models.TextChoices):
    ADMIN = "admin", "管理员"
    UPLOADER = "uploader", "上传者"
    USER = "user", "普通用户"


class UserStatus(models.TextChoices):
    ACTIVE = "active", "正常"
    DISABLED = "disabled", "禁用"


class User(AbstractUser):
    display_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER)
    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    api_token = models.CharField(max_length=32, unique=True, default=generate_secret_token)
    theme_mode = models.CharField(max_length=20, default="system")
    theme_custom_css = models.TextField(blank=True, default="")

    class Meta:
        db_table = "users"
        ordering = ["-date_joined", "-id"]

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.username
        if not self.api_token:
            self.api_token = generate_secret_token()
        super().save(*args, **kwargs)

    @property
    def is_active_member(self) -> bool:
        return self.status == UserStatus.ACTIVE


class InviteCode(models.Model):
    code = models.CharField(max_length=14, unique=True)
    note = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_invite_codes",
    )
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="used_invite_codes",
    )
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invite_codes"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return self.code

    @property
    def state(self) -> str:
        if self.used_at:
            return "used"
        if not self.is_active:
            return "revoked"
        if self.expires_at and self.expires_at <= timezone.now():
            return "expired"
        return "available"
