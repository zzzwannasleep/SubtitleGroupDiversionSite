from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.security import verify_password
from app.models.category import Category
from app.models.torrent import Torrent
from app.models.user import User, UserRole, UserStatus


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


def configure_internal_admin(app) -> None:
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=InternalAdminAuth(),
        base_url="/internal-admin",
        title="PT Platform Admin",
    )
    admin.add_view(UserAdminView)
    admin.add_view(CategoryAdminView)
    admin.add_view(TorrentAdminView)
