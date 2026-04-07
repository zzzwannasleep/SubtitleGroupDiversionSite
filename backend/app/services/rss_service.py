from __future__ import annotations

from email.utils import format_datetime
from urllib.parse import urlencode
from xml.sax.saxutils import escape

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.category import Category
from app.models.torrent import Torrent
from app.models.user import User, UserStatus
from app.services.torrent_query_service import apply_torrent_filters, apply_torrent_sort


class RssFeedError(ValueError):
    """Raised when RSS key validation or feed generation fails."""


def get_rss_user(db: Session, key: str) -> User:
    user = db.scalar(select(User).where(User.rss_key == key, User.status == UserStatus.ACTIVE))
    if user is None:
        raise RssFeedError("Invalid RSS key")
    return user


def build_rss_feed_url(
    *,
    base_url: str,
    key: str,
    category_slug: str | None = None,
    keyword: str | None = None,
    free_only: bool = False,
    sort: str = "created_at_desc",
) -> str:
    params: list[tuple[str, str]] = [("key", key)]

    if category_slug:
        params.append(("category", category_slug))

    normalized_keyword = keyword.strip() if keyword else ""
    if normalized_keyword:
        params.append(("keyword", normalized_keyword))

    if free_only:
        params.append(("free_only", "1"))

    if sort != "created_at_desc":
        params.append(("sort", sort))

    return f"{base_url}/rss/torrents?{urlencode(params)}"


def build_rss_feed_xml(
    db: Session,
    *,
    key: str,
    category_slug: str | None = None,
    keyword: str | None = None,
    free_only: bool = False,
    sort: str = "created_at_desc",
    base_url: str | None = None,
) -> str:
    settings = get_settings()
    user = get_rss_user(db, key)
    category = None

    if category_slug:
        category = db.scalar(select(Category).where(Category.slug == category_slug))

    statement = (
        select(Torrent)
        .options(joinedload(Torrent.category), joinedload(Torrent.owner), joinedload(Torrent.stats_cache))
        .where(Torrent.is_visible.is_(True))
    )
    statement = apply_torrent_filters(statement, category_slug=category_slug, keyword=keyword, free_only=free_only)
    statement = apply_torrent_sort(statement, sort=sort)

    torrents = db.scalars(statement).unique().all()
    base_url = (base_url or settings.public_web_base_url).rstrip("/")
    channel_title = "PT Platform Torrents"
    channel_link = f"{base_url}/torrents"
    channel_feed_url = build_rss_feed_url(
        base_url=base_url,
        key=user.rss_key,
        category_slug=category_slug,
        keyword=keyword,
        free_only=free_only,
        sort=sort,
    )

    if category_slug:
        category_name = category.name if category is not None else category_slug
        channel_title = f"PT Platform {category_name} Torrents"

    channel_query: list[tuple[str, str]] = []
    if category_slug:
        channel_query.append(("category", category_slug))
    normalized_keyword = keyword.strip() if keyword else ""
    if normalized_keyword:
        channel_query.append(("keyword", normalized_keyword))
    if free_only:
        channel_query.append(("free_only", "1"))
    if sort != "created_at_desc":
        channel_query.append(("sort", sort))

    if channel_query:
        channel_link = f"{channel_link}?{urlencode(channel_query)}"

    description_fragments = ["Private torrent feed", "all visible matches"]
    if normalized_keyword:
        description_fragments.append(f'keyword="{normalized_keyword}"')
    if category_slug:
        description_fragments.append(f"category={category_slug}")
    if free_only:
        description_fragments.append("free_only=true")

    items_xml = []
    for torrent in torrents:
        detail_url = f"{base_url}/torrents/{torrent.id}"
        download_url = f"{base_url}/rss/download/{torrent.id}?key={user.rss_key}"
        description = escape(torrent.subtitle or torrent.description or torrent.name)
        pub_date = format_datetime(torrent.created_at)
        title = escape(torrent.name)
        guid = escape(detail_url)
        items_xml.append(
            "\n".join(
                [
                    "    <item>",
                    f"      <title>{title}</title>",
                    f"      <link>{escape(detail_url)}</link>",
                    f'      <guid isPermaLink="true">{guid}</guid>',
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
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
            "  <channel>",
            f"    <title>{escape(channel_title)}</title>",
            f"    <link>{escape(channel_link)}</link>",
            f'    <atom:link href="{escape(channel_feed_url)}" rel="self" type="application/rss+xml" />',
            f"    <description>{escape(' | '.join(description_fragments))}</description>",
            *items_xml,
            "  </channel>",
            "</rss>",
        ]
    )
