from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.audit_log import AuditLog
from app.models.user import UserRole, UserStatus
from app.schemas.site import SiteSettingsResponse, SiteSettingsUpdateRequest


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


class AdminAuditLogActor(BaseModel):
    id: int
    username: str


class AdminAuditLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    actor: AdminAuditLogActor | None
    action: str
    target_type: str
    target_id: int | None
    details: dict[str, object] | None
    ip: str | None
    created_at: datetime

    @classmethod
    def from_audit_log(cls, audit_log: AuditLog) -> "AdminAuditLogItem":
        actor = None
        if audit_log.actor is not None:
            actor = AdminAuditLogActor(id=audit_log.actor.id, username=audit_log.actor.username)
        return cls(
            id=audit_log.id,
            actor_id=audit_log.actor_id,
            actor=actor,
            action=audit_log.action,
            target_type=audit_log.target_type,
            target_id=audit_log.target_id,
            details=audit_log.details,
            ip=audit_log.ip,
            created_at=audit_log.created_at,
        )


class AdminAuditLogListResponse(BaseModel):
    items: list[AdminAuditLogItem]
    total: int
    page: int
    page_size: int


class AdminSiteSettingsResponse(SiteSettingsResponse):
    pass


class AdminSiteSettingsUpdateRequest(SiteSettingsUpdateRequest):
    pass
