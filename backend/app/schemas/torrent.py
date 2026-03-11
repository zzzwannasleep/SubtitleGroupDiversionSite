from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class TorrentOwnerRead(BaseModel):
    id: int
    username: str


class TorrentStatsRead(BaseModel):
    seeders: int = 0
    leechers: int = 0
    snatches: int = 0
    finished: int = 0


class TorrentFileRead(BaseModel):
    file_path: str
    file_size_bytes: int


class TorrentListRead(BaseModel):
    id: int
    name: str
    subtitle: str | None = None
    category: str
    size_bytes: int
    owner: str
    seeders: int = 0
    leechers: int = 0
    snatches: int = 0
    created_at: datetime
    is_free: bool = False


class TorrentListResponse(BaseModel):
    items: list[TorrentListRead]
    total: int
    page: int
    page_size: int


class TorrentDetailRead(BaseModel):
    id: int
    name: str
    subtitle: str | None = None
    description: str | None = None
    info_hash: str
    size_bytes: int
    category: CategoryRead
    owner: TorrentOwnerRead
    stats: TorrentStatsRead
    files: list[TorrentFileRead]
    media_info: str | None = None
    nfo_text: str | None = None
    cover_image_url: str | None = None
    is_free: bool = False
    created_at: datetime


class TorrentUploadResponse(BaseModel):
    id: int | None = None
    info_hash: str | None = None
    message: str

