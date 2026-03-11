from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.database import get_db
from app.dependencies.auth import get_current_user_optional
from app.dependencies.roles import require_roles
from app.models.category import Category
from app.models.torrent import Torrent
from app.models.user import User, UserRole
from app.schemas.torrent import TorrentDetailRead, TorrentListResponse, TorrentUploadResponse
from app.services.torrent_service import build_torrent_detail, build_torrent_list_item


router = APIRouter(prefix="/api/torrents", tags=["torrents"])
settings = get_settings()


def _ensure_list_access(current_user: User | None) -> None:
    if not settings.allow_public_torrent_list and current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


@router.get("", response_model=TorrentListResponse)
def list_torrents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    sort: str = Query(default="created_at_desc"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> TorrentListResponse:
    _ensure_list_access(current_user)

    statement: Select[tuple[Torrent]] = (
        select(Torrent)
        .options(joinedload(Torrent.category), joinedload(Torrent.owner), joinedload(Torrent.stats_cache))
        .where(Torrent.is_visible.is_(True))
    )

    if category:
        statement = statement.join(Torrent.category).where(Category.slug == category)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        statement = statement.where(or_(Torrent.name.ilike(pattern), Torrent.subtitle.ilike(pattern)))

    if sort == "created_at_asc":
        statement = statement.order_by(Torrent.created_at.asc())
    else:
        statement = statement.order_by(Torrent.created_at.desc())

    count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
    total = db.scalar(count_statement) or 0
    torrents = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all()

    return TorrentListResponse(
        items=[build_torrent_list_item(torrent) for torrent in torrents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{torrent_id}", response_model=TorrentDetailRead)
def get_torrent_detail(
    torrent_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> TorrentDetailRead:
    _ensure_list_access(current_user)
    statement = (
        select(Torrent)
        .options(
            joinedload(Torrent.category),
            joinedload(Torrent.owner),
            joinedload(Torrent.files),
            joinedload(Torrent.stats_cache),
        )
        .where(Torrent.id == torrent_id, Torrent.is_visible.is_(True))
    )
    torrent = db.scalars(statement).unique().first()
    if torrent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Torrent not found")
    return build_torrent_detail(torrent)


@router.post(
    "/upload",
    response_model=TorrentUploadResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.UPLOADER))],
)
def upload_torrent() -> TorrentUploadResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Upload flow is not implemented yet")


@router.get("/{torrent_id}/download")
def download_torrent(
    torrent_id: int,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.UPLOADER, UserRole.USER)),
) -> dict[str, int | str]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Torrent rewrite/download is not implemented yet for torrent {torrent_id}",
    )

