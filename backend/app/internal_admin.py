from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.security import verify_password
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.torrent import Torrent
from app.models.user import User, UserRole, UserStatus
from app.services.admin_user_service import (
    LastActiveAdminError,
    coerce_user_role,
    coerce_user_status,
    ensure_not_removing_last_active_admin,
)
from app.services.site_settings_service import get_or_create_site_settings
from app.services.xbt_tracker_service import XbtTrackerError, upsert_xbt_user


internal_admin: Admin | None = None


def build_internal_admin_title(site_name: str | None) -> str:
    normalized_name = (site_name or "").strip()
    return f"{normalized_name} Admin" if normalized_name else "Site Admin"


def set_internal_admin_title(site_name: str | None) -> None:
    if internal_admin is not None:
        internal_admin.title = build_internal_admin_title(site_name)


def sync_internal_admin_title() -> None:
    try:
        with SessionLocal() as db:
            site_settings = get_or_create_site_settings(db)
            set_internal_admin_title(site_settings.site_name)
    except Exception:
        set_internal_admin_title(None)


class InternalAdminAuth(AuthenticationBackend):
    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(secret_key=settings.secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        identifier = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))
        if not identifier or not password:
            return False

        with SessionLocal() as db:
            user = db.scalar(select(User).where((User.username == identifier) | (User.email == identifier)))
            if user is None or not verify_password(password, user.password_hash):
                return False
            if user.role != UserRole.ADMIN or user.status != UserStatus.ACTIVE:
                return False

            user.last_login_at = datetime.now(UTC)
            db.add(user)
            db.commit()
            request.session.update({"internal_admin_user_id": user.id})
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("internal_admin_user_id")
        if not isinstance(user_id, int):
            return False

        with SessionLocal() as db:
            user = db.get(User, user_id)
            if user is None or user.role != UserRole.ADMIN or user.status != UserStatus.ACTIVE:
                request.session.clear()
                return False
            return True


class UserAdminView(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    can_create = False
    can_delete = False
    can_view_details = True
    column_list = [
        User.id,
        User.username,
        User.email,
        User.role,
        User.status,
        User.created_at,
        User.last_login_at,
    ]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.email, User.role, User.status, User.created_at]
    form_columns = [User.username, User.email, User.role, User.status]

    async def on_model_change(self, data: dict[str, Any], model: User, is_created: bool, request: Request) -> None:
        if is_created or model.id is None:
            return

        with SessionLocal() as db:
            persisted_user = db.get(User, model.id)
            if persisted_user is None:
                raise ValueError("User not found")

            try:
                target_role = coerce_user_role(data.get("role")) or persisted_user.role
                target_status = coerce_user_status(data.get("status")) or persisted_user.status
                ensure_not_removing_last_active_admin(db, persisted_user, target_role, target_status)
            except (LastActiveAdminError, ValueError) as exc:
                raise ValueError(str(exc)) from exc

            persisted_user.role = target_role
            persisted_user.status = target_status
            try:
                upsert_xbt_user(persisted_user)
            except XbtTrackerError as exc:
                raise ValueError(f"XBT user sync failed: {exc}") from exc


class CategoryAdminView(ModelView, model=Category):
    name = "Category"
    name_plural = "Categories"
    icon = "fa-solid fa-folder-tree"
    can_delete = False
    can_view_details = True
    column_list = [Category.id, Category.name, Category.slug, Category.sort_order, Category.is_enabled, Category.created_at]
    column_searchable_list = [Category.name, Category.slug]
    column_sortable_list = [Category.id, Category.name, Category.slug, Category.sort_order, Category.created_at]
    form_columns = [Category.name, Category.slug, Category.sort_order, Category.is_enabled]


class TorrentAdminView(ModelView, model=Torrent):
    name = "Torrent"
    name_plural = "Torrents"
    icon = "fa-solid fa-compact-disc"
    can_create = False
    can_delete = False
    can_view_details = True
    column_list = [
        Torrent.id,
        Torrent.name,
        Torrent.category,
        Torrent.owner,
        Torrent.info_hash,
        Torrent.size_bytes,
        Torrent.is_visible,
        Torrent.is_free,
        Torrent.created_at,
    ]
    column_searchable_list = [Torrent.name, Torrent.subtitle, Torrent.info_hash]
    column_sortable_list = [
        Torrent.id,
        Torrent.name,
        Torrent.info_hash,
        Torrent.size_bytes,
        Torrent.is_visible,
        Torrent.is_free,
        Torrent.created_at,
    ]
    form_columns = [
        Torrent.name,
        Torrent.subtitle,
        Torrent.description,
        Torrent.category,
        Torrent.cover_image_url,
        Torrent.media_info,
        Torrent.nfo_text,
        Torrent.is_visible,
        Torrent.is_free,
    ]


class AuditLogAdminView(ModelView, model=AuditLog):
    name = "Audit Log"
    name_plural = "Audit Logs"
    icon = "fa-solid fa-clipboard-list"
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_list = [
        AuditLog.id,
        AuditLog.actor,
        AuditLog.action,
        AuditLog.target_type,
        AuditLog.target_id,
        AuditLog.ip,
        AuditLog.created_at,
    ]
    column_searchable_list = [AuditLog.action, AuditLog.target_type, AuditLog.ip]
    column_sortable_list = [AuditLog.id, AuditLog.action, AuditLog.target_type, AuditLog.created_at]


def configure_internal_admin(app) -> None:
    global internal_admin

    internal_admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=InternalAdminAuth(),
        base_url="/internal-admin",
        title=build_internal_admin_title(None),
    )
    internal_admin.add_view(UserAdminView)
    internal_admin.add_view(CategoryAdminView)
    internal_admin.add_view(TorrentAdminView)
    internal_admin.add_view(AuditLogAdminView)
