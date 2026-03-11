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


class AdminCategoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    sort_order: int
    is_enabled: bool
    created_at: datetime


class AdminCategoryCreateRequest(BaseModel):
    name: str
    slug: str
    sort_order: int = 0
    is_enabled: bool = True


class AdminCategoryUpdateRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    sort_order: int | None = None
    is_enabled: bool | None = None


class AdminTorrentListItem(BaseModel):
    id: int
    name: str
    category: str
    owner: str
    info_hash: str
    is_visible: bool
    is_free: bool
    created_at: datetime


class AdminTorrentListResponse(BaseModel):
    items: list[AdminTorrentListItem]
    total: int
    page: int
    page_size: int


class AdminTorrentUpdateRequest(BaseModel):
    is_visible: bool | None = None
    is_free: bool | None = None
    category_id: int | None = None


class AdminTrackerSyncResponse(BaseModel):
    user_stats_updated: int
    torrent_stats_updated: int
    skipped: bool = False
    message: str
