from __future__ import annotations

from sqlalchemy import Select, or_

from app.models.category import Category
from app.models.torrent import Torrent


def apply_torrent_filters(
    statement: Select[tuple[Torrent]],
    *,
    category_slug: str | None = None,
    keyword: str | None = None,
    free_only: bool = False,
) -> Select[tuple[Torrent]]:
    if category_slug:
        statement = statement.join(Torrent.category).where(Category.slug == category_slug)

    normalized_keyword = keyword.strip() if keyword else ""
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        statement = statement.where(or_(Torrent.name.ilike(pattern), Torrent.subtitle.ilike(pattern)))

    if free_only:
        statement = statement.where(Torrent.is_free.is_(True))

    return statement


def apply_torrent_sort(statement: Select[tuple[Torrent]], *, sort: str = "created_at_desc") -> Select[tuple[Torrent]]:
    if sort == "created_at_asc":
        return statement.order_by(Torrent.created_at.asc())
    return statement.order_by(Torrent.created_at.desc())
