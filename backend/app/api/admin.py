from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.dependencies.admin import require_admin
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.torrent import Torrent
from app.models.user import User
from app.schemas.admin import (
    AdminAuditLogItem,
    AdminAuditLogListResponse,
    AdminCategoryCreateRequest,
    AdminCategoryItem,
    AdminSiteSettingsResponse,
    AdminSiteSettingsUpdateRequest,
    AdminCategoryUpdateRequest,
    AdminTorrentListItem,
    AdminTorrentListResponse,
    AdminTorrentUpdateRequest,
    AdminTrackerSyncResponse,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserUpdateRequest,
)
from app.internal_admin import set_internal_admin_title
from app.services.admin_user_service import LastActiveAdminError, ensure_not_removing_last_active_admin
from app.services.audit_log_service import record_admin_audit_log
from app.services.site_settings_service import get_or_create_site_settings
from app.services.tracker_sync_service import TrackerSyncError, sync_tracker_stats
from app.services.xbt_tracker_service import XbtTrackerError, upsert_xbt_user


router = APIRouter(prefix="/api/admin", tags=["admin"])


def _audit_value(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    return value


def _audit_change(before: Any, after: Any) -> dict[str, Any]:
    return {"from": _audit_value(before), "to": _audit_value(after)}


@router.get("/site-settings", response_model=AdminSiteSettingsResponse)
def get_admin_site_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminSiteSettingsResponse:
    return AdminSiteSettingsResponse.model_validate(get_or_create_site_settings(db))


@router.patch("/site-settings", response_model=AdminSiteSettingsResponse)
def update_admin_site_settings(
    payload: AdminSiteSettingsUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminSiteSettingsResponse:
    site_settings = get_or_create_site_settings(db)
    previous_site_name = site_settings.site_name
    site_name = payload.site_name.strip()
    if not site_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site name cannot be empty")

    site_settings.site_name = site_name
    db.add(site_settings)
    if previous_site_name != site_settings.site_name:
        record_admin_audit_log(
            db,
            actor=current_user,
            action="site_settings.update",
            target_type="site_settings",
            target_id=site_settings.id,
            details={"changes": {"site_name": _audit_change(previous_site_name, site_settings.site_name)}},
            request=request,
        )
    db.commit()
    db.refresh(site_settings)
    set_internal_admin_title(site_settings.site_name)
    return AdminSiteSettingsResponse.model_validate(site_settings)


def _build_admin_torrent_item(torrent: Torrent) -> AdminTorrentListItem:
    return AdminTorrentListItem(
        id=torrent.id,
        name=torrent.name,
        category=torrent.category.name,
        owner=torrent.owner.username,
        info_hash=torrent.info_hash,
        is_visible=torrent.is_visible,
        is_free=torrent.is_free,
        created_at=torrent.created_at,
    )


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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminUserListItem:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    target_role = payload.role if payload.role is not None else user.role
    target_status = payload.status if payload.status is not None else user.status
    try:
        ensure_not_removing_last_active_admin(db, user, target_role, target_status)
    except LastActiveAdminError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    changes: dict[str, dict[str, Any]] = {}
    if payload.role is not None:
        if payload.role != user.role:
            changes["role"] = _audit_change(user.role, payload.role)
        user.role = payload.role

    if payload.status is not None:
        if payload.status != user.status:
            changes["status"] = _audit_change(user.status, payload.status)
        user.status = payload.status

    db.add(user)
    if changes:
        record_admin_audit_log(
            db,
            actor=current_user,
            action="user.update",
            target_type="user",
            target_id=user.id,
            details={"changes": changes},
            request=request,
        )
    try:
        upsert_xbt_user(user)
        db.commit()
        db.refresh(user)
    except XbtTrackerError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"XBT user sync failed: {exc}") from exc
    return AdminUserListItem.model_validate(user)


@router.get("/categories", response_model=list[AdminCategoryItem])
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[AdminCategoryItem]:
    categories = db.scalars(select(Category).order_by(Category.sort_order, Category.name)).all()
    return [AdminCategoryItem.model_validate(category) for category in categories]


@router.post("/categories", response_model=AdminCategoryItem, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: AdminCategoryCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminCategoryItem:
    name = payload.name.strip()
    slug = payload.slug.strip().lower()
    if not name or not slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name and slug are required")

    existing_category = db.scalar(select(Category).where((Category.name == name) | (Category.slug == slug)))
    if existing_category is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name or slug already exists")

    category = Category(name=name, slug=slug, sort_order=payload.sort_order, is_enabled=payload.is_enabled)
    db.add(category)
    db.flush()
    record_admin_audit_log(
        db,
        actor=current_user,
        action="category.create",
        target_type="category",
        target_id=category.id,
        details={
            "category": {
                "name": category.name,
                "slug": category.slug,
                "sort_order": category.sort_order,
                "is_enabled": category.is_enabled,
            }
        },
        request=request,
    )
    db.commit()
    db.refresh(category)
    return AdminCategoryItem.model_validate(category)


@router.patch("/categories/{category_id}", response_model=AdminCategoryItem)
def update_category(
    category_id: int,
    payload: AdminCategoryUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminCategoryItem:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    changes: dict[str, dict[str, Any]] = {}
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name cannot be empty")
        if name != category.name:
            changes["name"] = _audit_change(category.name, name)
        category.name = name

    if payload.slug is not None:
        slug = payload.slug.strip().lower()
        if not slug:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category slug cannot be empty")
        existing_category = db.scalar(select(Category).where(Category.slug == slug, Category.id != category_id))
        if existing_category is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category slug already exists")
        if slug != category.slug:
            changes["slug"] = _audit_change(category.slug, slug)
        category.slug = slug

    if payload.sort_order is not None:
        if payload.sort_order != category.sort_order:
            changes["sort_order"] = _audit_change(category.sort_order, payload.sort_order)
        category.sort_order = payload.sort_order

    if payload.is_enabled is not None:
        if payload.is_enabled != category.is_enabled:
            changes["is_enabled"] = _audit_change(category.is_enabled, payload.is_enabled)
        category.is_enabled = payload.is_enabled

    db.add(category)
    if changes:
        record_admin_audit_log(
            db,
            actor=current_user,
            action="category.update",
            target_type="category",
            target_id=category.id,
            details={"changes": changes},
            request=request,
        )
    db.commit()
    db.refresh(category)
    return AdminCategoryItem.model_validate(category)


@router.get("/torrents", response_model=AdminTorrentListResponse)
def list_torrents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    category_id: int | None = Query(default=None, ge=1),
    is_visible: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminTorrentListResponse:
    statement: Select[tuple[Torrent]] = select(Torrent).options(joinedload(Torrent.category), joinedload(Torrent.owner))

    if keyword:
        pattern = f"%{keyword.strip()}%"
        statement = statement.where(or_(Torrent.name.ilike(pattern), Torrent.subtitle.ilike(pattern)))
    if category_id is not None:
        statement = statement.where(Torrent.category_id == category_id)
    if is_visible is not None:
        statement = statement.where(Torrent.is_visible.is_(is_visible))

    statement = statement.order_by(Torrent.created_at.desc())
    count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
    total = db.scalar(count_statement) or 0
    torrents = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all()

    return AdminTorrentListResponse(
        items=[_build_admin_torrent_item(torrent) for torrent in torrents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/torrents/{torrent_id}", response_model=AdminTorrentListItem)
def update_torrent(
    torrent_id: int,
    payload: AdminTorrentUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminTorrentListItem:
    torrent = db.scalar(
        select(Torrent)
        .options(joinedload(Torrent.category), joinedload(Torrent.owner))
        .where(Torrent.id == torrent_id)
    )
    if torrent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Torrent not found")

    changes: dict[str, dict[str, Any]] = {}
    if payload.category_id is not None:
        category = db.get(Category, payload.category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")
        if payload.category_id != torrent.category_id:
            changes["category_id"] = _audit_change(torrent.category_id, payload.category_id)
        torrent.category_id = payload.category_id

    if payload.is_visible is not None:
        if payload.is_visible != torrent.is_visible:
            changes["is_visible"] = _audit_change(torrent.is_visible, payload.is_visible)
        torrent.is_visible = payload.is_visible

    if payload.is_free is not None:
        if payload.is_free != torrent.is_free:
            changes["is_free"] = _audit_change(torrent.is_free, payload.is_free)
        torrent.is_free = payload.is_free

    db.add(torrent)
    if changes:
        record_admin_audit_log(
            db,
            actor=current_user,
            action="torrent.update",
            target_type="torrent",
            target_id=torrent.id,
            details={"changes": changes},
            request=request,
        )
    db.commit()

    refreshed_torrent = db.scalar(
        select(Torrent)
        .options(joinedload(Torrent.category), joinedload(Torrent.owner))
        .where(Torrent.id == torrent_id)
    )
    if refreshed_torrent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Torrent not found")
    return _build_admin_torrent_item(refreshed_torrent)


@router.post("/tracker/sync", response_model=AdminTrackerSyncResponse)
def trigger_tracker_sync(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminTrackerSyncResponse:
    try:
        result = sync_tracker_stats(db)
    except TrackerSyncError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    record_admin_audit_log(
        db,
        actor=current_user,
        action="tracker.sync",
        target_type="tracker",
        details={"result": result},
        request=request,
    )
    db.commit()
    return AdminTrackerSyncResponse(**result)


@router.get("/audit-logs", response_model=AdminAuditLogListResponse)
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminAuditLogListResponse:
    statement = select(AuditLog).options(joinedload(AuditLog.actor)).order_by(AuditLog.created_at.desc())
    count_statement = select(func.count()).select_from(AuditLog)
    total = db.scalar(count_statement) or 0
    audit_logs = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return AdminAuditLogListResponse(
        items=[AdminAuditLogItem.from_audit_log(audit_log) for audit_log in audit_logs],
        total=total,
        page=page,
        page_size=page_size,
    )
