from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from starlette.requests import Request

from app.models.audit_log import AuditLog
from app.models.user import User


def get_request_ip(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None
    return request.client.host


def record_admin_audit_log(
    db: Session,
    *,
    actor: User,
    action: str,
    target_type: str,
    target_id: int | None = None,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_id=actor.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or None,
        ip=get_request_ip(request),
    )
    db.add(audit_log)
    return audit_log
