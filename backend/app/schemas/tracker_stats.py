from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TrackerUserStatsRead(BaseModel):
    uploaded_bytes: int
    downloaded_bytes: int
    ratio: Decimal | None
    updated_at: datetime


class TrackerTorrentStatsRead(BaseModel):
    seeders: int
    leechers: int
    snatches: int
    finished: int
    updated_at: datetime
