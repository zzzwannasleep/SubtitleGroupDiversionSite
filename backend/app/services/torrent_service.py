from app.models.torrent import Torrent
from app.schemas.torrent import (
    CategoryRead,
    TorrentDetailRead,
    TorrentFileRead,
    TorrentListRead,
    TorrentOwnerRead,
    TorrentStatsRead,
)


def build_torrent_list_item(torrent: Torrent) -> TorrentListRead:
    stats = torrent.stats_cache
    return TorrentListRead(
        id=torrent.id,
        name=torrent.name,
        subtitle=torrent.subtitle,
        category=torrent.category.name,
        size_bytes=torrent.size_bytes,
        owner=torrent.owner.username,
        seeders=stats.seeders if stats else 0,
        leechers=stats.leechers if stats else 0,
        snatches=stats.snatches if stats else 0,
        created_at=torrent.created_at,
        is_free=torrent.is_free,
    )


def build_torrent_detail(torrent: Torrent) -> TorrentDetailRead:
    stats = torrent.stats_cache
    return TorrentDetailRead(
        id=torrent.id,
        name=torrent.name,
        subtitle=torrent.subtitle,
        description=torrent.description,
        info_hash=torrent.info_hash,
        size_bytes=torrent.size_bytes,
        category=CategoryRead.model_validate(torrent.category),
        owner=TorrentOwnerRead(id=torrent.owner.id, username=torrent.owner.username),
        stats=TorrentStatsRead(
            seeders=stats.seeders if stats else 0,
            leechers=stats.leechers if stats else 0,
            snatches=stats.snatches if stats else 0,
            finished=stats.finished if stats else 0,
        ),
        files=[TorrentFileRead(file_path=file.file_path, file_size_bytes=file.file_size_bytes) for file in torrent.files],
        media_info=torrent.media_info,
        nfo_text=torrent.nfo_text,
        cover_image_url=torrent.cover_image_url,
        is_free=torrent.is_free,
        created_at=torrent.created_at,
    )

