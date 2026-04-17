import secrets

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import AuditService
from apps.common.utils import generate_secret_token
from apps.users.models import InviteCode, User, generate_invite_code, normalize_invite_code


class UserService:
    @staticmethod
    def create_user(*, actor, username: str, display_name: str, email: str, role: str, password: str | None = None):
        generated_password = None
        effective_password = password
        if not effective_password:
            generated_password = secrets.token_urlsafe(12)[:12]
            effective_password = generated_password

        with transaction.atomic():
            user = User.objects.create(
                username=username,
                display_name=display_name,
                email=email,
                role=role,
            )
            user.set_password(effective_password)
            user.save(update_fields=["password"])
            AuditService.log(
                actor,
                "创建用户",
                "用户",
                user.username,
                detail=f"角色：{user.role}",
                payload={"user_id": user.id},
            )

        return user, generated_password

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
    def reset_api_token(*, actor, user: User):
        with transaction.atomic():
            user.api_token = generate_secret_token()
            user.save(update_fields=["api_token"])
            AuditService.log(
                actor,
                "重置 API token",
                "用户",
                user.username,
                detail="API token 已重置，旧的内部脚本凭证失效。",
                payload={"user_id": user.id},
            )

        return user


class InviteCodeService:
    @staticmethod
    def _generate_unique_code() -> str:
        code = generate_invite_code()
        while InviteCode.objects.filter(code=code).exists():
            code = generate_invite_code()
        return code

    @staticmethod
    def create_codes(*, actor, count: int, note: str = "", expires_at=None) -> list[InviteCode]:
        created_codes: list[InviteCode] = []

        with transaction.atomic():
            for _ in range(count):
                created_codes.append(
                    InviteCode.objects.create(
                        code=InviteCodeService._generate_unique_code(),
                        note=note,
                        expires_at=expires_at,
                        created_by=actor if getattr(actor, "pk", None) else None,
                    )
                )

            AuditService.log(
                actor,
                "生成邀请码",
                "邀请码",
                f"{count} 个邀请码",
                detail=f"共生成 {count} 个邀请码。",
                payload={
                    "count": count,
                    "invite_code_ids": [item.id for item in created_codes],
                    "expires_at": expires_at.isoformat() if expires_at else None,
                },
            )

        return created_codes

    @staticmethod
    def redeem_code(*, raw_code: str, user: User) -> InviteCode:
        with transaction.atomic():
            normalized_code = normalize_invite_code(raw_code)
            invite_code = InviteCode.objects.select_for_update().filter(code=normalized_code).first()

            if not invite_code:
                raise ValidationError("邀请码不存在。")
            if invite_code.used_at:
                raise ValidationError("邀请码已被使用。")
            if not invite_code.is_active:
                raise ValidationError("邀请码已被停用。")
            if invite_code.expires_at and invite_code.expires_at <= timezone.now():
                raise ValidationError("邀请码已过期。")

            invite_code.used_by = user
            invite_code.used_at = timezone.now()
            invite_code.is_active = False
            invite_code.save(update_fields=["used_by", "used_at", "is_active"])

            AuditService.log(
                user,
                "使用邀请码注册",
                "邀请码",
                invite_code.code,
                detail=f"邀请码已被用户 {user.username} 使用。",
                payload={"invite_code_id": invite_code.id, "user_id": user.id},
            )

            return invite_code

    @staticmethod
    def revoke_code(*, actor, invite_code: InviteCode) -> InviteCode:
        with transaction.atomic():
            locked_code = InviteCode.objects.select_for_update().get(pk=invite_code.pk)

            if locked_code.used_at:
                raise ValidationError("已使用的邀请码无法停用。")
            if not locked_code.is_active:
                return locked_code

            locked_code.is_active = False
            locked_code.save(update_fields=["is_active"])
            AuditService.log(
                actor,
                "停用邀请码",
                "邀请码",
                locked_code.code,
                detail="邀请码已停用。",
                payload={"invite_code_id": locked_code.id},
            )

            return locked_code
