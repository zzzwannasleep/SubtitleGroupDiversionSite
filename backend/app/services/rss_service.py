from __future__ import annotations

from email.utils import format_datetime
from xml.sax.saxutils import escape

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.category import Category
from app.models.torrent import Torrent
from app.models.user import User


class RssFeedError(ValueError):
    """Raised when RSS key validation or feed generation fails."""


def get_rss_user(db: Session, key: str) -> User:
    user = db.scalar(select(User).where(User.rss_key == key))
    if user is None:
        raise RssFeedError("Invalid RSS key")
    return user


def build_rss_feed_xml(db: Session, *, key: str, category_slug: str | None = None) -> str:
    settings = get_settings()
    user = get_rss_user(db, key)

    statement = (
        select(Torrent)
        .options(joinedload(Torrent.category), joinedload(Torrent.owner), joinedload(Torrent.stats_cache))
        .where(Torrent.is_visible.is_(True))
        .order_by(Torrent.created_at.desc())
        .limit(50)
    )

    if category_slug:
        statement = statement.join(Torrent.category).where(Category.slug == category_slug)

    torrents = db.scalars(statement).unique().all()
    base_url = settings.public_web_base_url.rstrip("/")
    channel_title = "PT Platform Torrents" if category_slug is None else f"PT Platform {category_slug} Torrents"
    channel_link = f"{base_url}/torrents"

    items_xml = []
    for torrent in torrents:
        detail_url = f"{base_url}/torrents/{torrent.id}"
        download_url = f"{base_url}/rss/download/{torrent.id}?key={user.rss_key}"
        description = escape(torrent.subtitle or torrent.description or torrent.name)
        pub_date = format_datetime(torrent.created_at)
        title = escape(torrent.name)
        guid = escape(f"{base_url}/guid/torrents/{torrent.id}")
        items_xml.append(
            "\n".join(
                [
                    "    <item>",
                    f"      <title>{title}</title>",
                    f"      <link>{escape(detail_url)}</link>",
                    f"      <guid>{guid}</guid>",
                    f"      <pubDate>{pub_date}</pubDate>",
                    f"      <description>{description}</description>",
                    f'      <enclosure url="{escape(download_url)}" length="{torrent.size_bytes}" type="application/x-bittorrent" />',
                    "    </item>",
                ]
            )
        )

    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0">',
            "  <channel>",
            f"    <title>{escape(channel_title)}</title>",
            f"    <link>{escape(channel_link)}</link>",
            "    <description>Private torrent feed</description>",
            *items_xml,
            "  </channel>",
            "</rss>",
        ]
    )
