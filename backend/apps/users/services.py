import secrets

from django.db import transaction

from apps.audit.services import AuditService
from apps.common.utils import generate_passkey
from apps.tracker_sync.services import TrackerSyncService
from apps.users.models import User


class UserService:
    @staticmethod
    def create_user(*, actor, username: str, display_name: str, email: str, role: str):
        initial_password = secrets.token_urlsafe(12)[:12]
        with transaction.atomic():
            user = User.objects.create(
                username=username,
                display_name=display_name,
                email=email,
                role=role,
                passkey=generate_passkey(),
            )
            user.set_password(initial_password)
            user.save(update_fields=["password"])
            AuditService.log(
                actor,
                "创建用户",
                "用户",
                user.username,
                detail=f"角色：{user.role}",
                payload={"user_id": user.id},
            )
        TrackerSyncService.sync_user(user)
        return user, initial_password

    @staticmethod
    def change_status(*, actor, user: User, next_status: str):
        user.status = next_status
        user.save(update_fields=["status"])
        AuditService.log(
            actor,
            "启用用户" if next_status == "active" else "禁用用户",
            "用户",
            user.username,
            detail=f"状态切换为 {next_status}",
            payload={"user_id": user.id},
        )
        TrackerSyncService.sync_user(user)
        return user

    @staticmethod
    def reset_passkey(*, actor, user: User):
        user.passkey = generate_passkey()
        user.save(update_fields=["passkey"])
        AuditService.log(
            actor,
            "重置 passkey",
            "用户",
            user.username,
            detail="passkey 已重置，旧 RSS 与旧 torrent 失效。",
            payload={"user_id": user.id},
        )
        TrackerSyncService.sync_user(user)
        return user
