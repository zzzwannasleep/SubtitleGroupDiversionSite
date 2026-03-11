from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.database import get_db
from app.dependencies.auth import get_current_user_optional
from app.dependencies.roles import require_roles
from app.models.torrent import Torrent
from app.models.user import User, UserRole
from app.schemas.torrent import TorrentDetailRead, TorrentListResponse, TorrentUploadResponse
from app.services.torrent_query_service import apply_torrent_filters, apply_torrent_sort
from app.services.torrent_download_service import TorrentDownloadError, create_download_payload
from app.services.torrent_service import build_torrent_detail, build_torrent_list_item
from app.services.torrent_upload_service import TorrentUploadError, create_uploaded_torrent


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
    statement = apply_torrent_filters(statement, category_slug=category, keyword=keyword)
    statement = apply_torrent_sort(statement, sort=sort)

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
    status_code=status.HTTP_201_CREATED,
)
async def upload_torrent(
    torrent_file: UploadFile = File(...),
    category_id: int = Form(...),
    name: str | None = Form(default=None),
    subtitle: str | None = Form(default=None),
    description: str | None = Form(default=None),
    cover_image_url: str | None = Form(default=None),
    media_info: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.UPLOADER)),
) -> TorrentUploadResponse:
    file_bytes = await torrent_file.read()

    try:
        torrent, parsed = create_uploaded_torrent(
            db,
            current_user=current_user,
            filename=torrent_file.filename,
            file_bytes=file_bytes,
            category_id=category_id,
            name=name,
            subtitle=subtitle,
            description=description,
            cover_image_url=cover_image_url,
            media_info=media_info,
        )
    except TorrentUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return TorrentUploadResponse(id=torrent.id, info_hash=parsed.info_hash, message="uploaded")


@router.get("/{torrent_id}/download")
def download_torrent(
    request: Request,
    torrent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.UPLOADER, UserRole.USER)),
) -> Response:
    requester_ip = request.client.host if request.client else "unknown"

    try:
        rewritten_bytes, torrent = create_download_payload(
            db=db,
            torrent_id=torrent_id,
            user=current_user,
            requester_ip=requester_ip,
        )
    except TorrentDownloadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    filename = f"{torrent.info_hash}.torrent"
    return Response(
        content=rewritten_bytes,
        media_type="application/x-bittorrent",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
