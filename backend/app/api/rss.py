from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.rss_service import RssFeedError, build_rss_feed_xml, get_rss_user
from app.services.torrent_download_service import TorrentDownloadError, create_download_payload


router = APIRouter(prefix="/rss", tags=["rss"])


def get_request_base_url(request: Request) -> str:
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    host = forwarded_host or request.headers.get("host")
    scheme = forwarded_proto or request.url.scheme

    if host:
        return f"{scheme}://{host}"
    return str(request.base_url).rstrip("/")


@router.get("/torrents")
def rss_torrents(
    request: Request,
    key: str = Query(..., min_length=1),
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    free_only: bool = Query(default=False),
    sort: str = Query(default="created_at_desc"),
    db: Session = Depends(get_db),
) -> Response:
    try:
        payload = build_rss_feed_xml(
            db,
            key=key,
            category_slug=category,
            keyword=keyword,
            free_only=free_only,
            sort=sort,
            base_url=get_request_base_url(request),
        )
    except RssFeedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return Response(content=payload, media_type="application/rss+xml; charset=utf-8")


@router.get("/category/{slug}")
def rss_category(
    slug: str,
    request: Request,
    key: str = Query(..., min_length=1),
    keyword: str | None = Query(default=None),
    free_only: bool = Query(default=False),
    sort: str = Query(default="created_at_desc"),
    db: Session = Depends(get_db),
) -> Response:
    try:
        payload = build_rss_feed_xml(
            db,
            key=key,
            category_slug=slug,
            keyword=keyword,
            free_only=free_only,
            sort=sort,
            base_url=get_request_base_url(request),
        )
    except RssFeedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return Response(content=payload, media_type="application/rss+xml; charset=utf-8")


@router.get("/download/{torrent_id}")
def rss_download(
    torrent_id: int,
    request: Request,
    key: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> Response:
    try:
        user = get_rss_user(db, key)
    except RssFeedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    requester_ip = request.client.host if request.client else "unknown"

    try:
        rewritten_bytes, torrent = create_download_payload(
            db=db,
            torrent_id=torrent_id,
            user=user,
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
