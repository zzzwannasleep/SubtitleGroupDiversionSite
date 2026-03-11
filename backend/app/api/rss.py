from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.rss_service import RssFeedError, build_rss_feed_xml
from app.services.torrent_download_service import TorrentDownloadError, create_download_payload


router = APIRouter(prefix="/rss", tags=["rss"])


@router.get("/torrents")
def rss_torrents(
    key: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> Response:
    try:
        payload = build_rss_feed_xml(db, key=key)
    except RssFeedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return Response(content=payload, media_type="application/rss+xml; charset=utf-8")


@router.get("/category/{slug}")
def rss_category(
    slug: str,
    key: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> Response:
    try:
        payload = build_rss_feed_xml(db, key=key, category_slug=slug)
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
    user = db.scalar(select(User).where(User.rss_key == key))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid RSS key")

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
