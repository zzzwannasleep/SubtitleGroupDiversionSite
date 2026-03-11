from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole, UserStatus


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: UserRole


class AuthenticatedUserRead(UserRead):
    status: UserStatus
    tracker_credential: str
    rss_key: str
    created_at: datetime


class UserProfileRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    rss_key: str
    created_at: datetime
    tracker_credential: str
    uploaded_bytes: int = 0
    downloaded_bytes: int = 0
    ratio: Decimal | None = None

