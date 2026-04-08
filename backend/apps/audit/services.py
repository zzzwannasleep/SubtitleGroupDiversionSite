from apps.audit.models import AuditLog


class AuditService:
    @staticmethod
    def log(actor, action: str, target_type: str, target_name: str, detail: str = "", payload: dict | None = None):
        actor_name = getattr(actor, "display_name", None) or getattr(actor, "username", None) or "系统"
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "pk", None) else None,
            actor_name=actor_name,
            action=action,
            target_type=target_type,
            target_name=target_name,
            detail=detail,
            payload_json=payload or {},
        )
