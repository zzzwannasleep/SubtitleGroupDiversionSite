from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.admin import require_admin
from app.models.user import User, UserRole
from app.schemas.admin import AdminUserListItem, AdminUserListResponse, AdminUserUpdateRequest


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminUserListResponse:
    statement = select(User).order_by(User.created_at.desc())
    count_statement = select(func.count()).select_from(User)
    total = db.scalar(count_statement) or 0
    users = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return AdminUserListResponse(
        items=[AdminUserListItem.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}", response_model=AdminUserListItem)
def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> AdminUserListItem:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.role is not None:
        if user.id == current_admin.id and payload.role != UserRole.ADMIN:
            admin_count = db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)) or 0
            if admin_count <= 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote the last admin")
        user.role = payload.role

    if payload.status is not None:
        user.status = payload.status

    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminUserListItem.model_validate(user)
