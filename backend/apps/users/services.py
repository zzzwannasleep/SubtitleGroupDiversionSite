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
            transaction.on_commit(lambda: TrackerSyncService.sync_user_by_id(user.id))
        return user, initial_password

    @staticmethod
    def change_status(*, actor, user: User, next_status: str):
        with transaction.atomic():
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
            transaction.on_commit(lambda: TrackerSyncService.sync_user_by_id(user.id))
        return user

    @staticmethod
    def update_user(*, actor, user: User, display_name: str | None = None, email: str | None = None, role: str | None = None):
        changed_fields: list[str] = []
        changed_payload: dict[str, str] = {}

        if display_name is not None and display_name != user.display_name:
            user.display_name = display_name
            changed_fields.append("display_name")
            changed_payload["display_name"] = display_name
        if email is not None and email != user.email:
            user.email = email
            changed_fields.append("email")
            changed_payload["email"] = email
        if role is not None and role != user.role:
            user.role = role
            changed_fields.append("role")
            changed_payload["role"] = role

        if not changed_fields:
            return user

        with transaction.atomic():
            user.save(update_fields=changed_fields)
            AuditService.log(
                actor,
                "更新用户",
                "用户",
                user.username,
                detail=f"更新字段：{', '.join(changed_fields)}",
                payload={"user_id": user.id, "changes": changed_payload},
            )
        return user

    @staticmethod
    def reset_passkey(*, actor, user: User):
        with transaction.atomic():
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
            transaction.on_commit(lambda: TrackerSyncService.sync_user_by_id(user.id))
        return user
