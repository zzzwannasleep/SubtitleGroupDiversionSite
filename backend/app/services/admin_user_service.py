from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStatus


class LastActiveAdminError(ValueError):
    """Raised when a change would remove the final active admin."""


def coerce_user_role(value: UserRole | str | None) -> UserRole | None:
    if value is None:
        return None
    if isinstance(value, UserRole):
        return value
    raw_value = str(value)
    try:
        return UserRole(raw_value)
    except ValueError:
        return UserRole[raw_value.upper()]


def coerce_user_status(value: UserStatus | str | None) -> UserStatus | None:
    if value is None:
        return None
    if isinstance(value, UserStatus):
        return value
    raw_value = str(value)
    try:
        return UserStatus(raw_value)
    except ValueError:
        return UserStatus[raw_value.upper()]


def ensure_not_removing_last_active_admin(
    db: Session,
    user: User,
    target_role: UserRole,
    target_status: UserStatus,
) -> None:
    will_remove_active_admin = (
        user.role == UserRole.ADMIN
        and user.status == UserStatus.ACTIVE
        and (target_role != UserRole.ADMIN or target_status != UserStatus.ACTIVE)
    )

    if not will_remove_active_admin:
        return

    active_admin_count = (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == UserRole.ADMIN, User.status == UserStatus.ACTIVE)
        )
        or 0
    )
    if active_admin_count <= 1:
        raise LastActiveAdminError("Cannot demote or disable the last active admin")
