from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole, UserStatus


class AdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: UserRole
    status: UserStatus
    created_at: datetime


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    page_size: int


class AdminUserUpdateRequest(BaseModel):
    role: UserRole | None = None
    status: UserStatus | None = None

