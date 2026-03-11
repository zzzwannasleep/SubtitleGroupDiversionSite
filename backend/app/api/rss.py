from fastapi import APIRouter, HTTPException, status


router = APIRouter(prefix="/rss", tags=["rss"])


@router.get("/torrents")
def rss_torrents() -> dict[str, str]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="RSS feed is not implemented yet")


@router.get("/category/{slug}")
def rss_category(slug: str) -> dict[str, str]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Category RSS feed is not implemented yet for {slug}",
    )


@router.get("/download/{torrent_id}")
def rss_download(torrent_id: int) -> dict[str, str]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"RSS download endpoint is not implemented yet for torrent {torrent_id}",
    )

