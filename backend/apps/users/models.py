from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.utils import generate_passkey


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
    passkey = models.CharField(max_length=32, unique=True, default=generate_passkey)

    class Meta:
        db_table = "users"
        ordering = ["-date_joined", "-id"]

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.username
        if not self.passkey:
            self.passkey = generate_passkey()
        super().save(*args, **kwargs)

    @property
    def is_active_member(self) -> bool:
        return self.status == UserStatus.ACTIVE
