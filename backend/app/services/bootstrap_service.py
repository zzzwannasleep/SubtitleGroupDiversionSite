from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category


DEFAULT_CATEGORIES = [
    {"name": "Movies", "slug": "movies", "sort_order": 10},
    {"name": "TV Shows", "slug": "tv-shows", "sort_order": 20},
    {"name": "Anime", "slug": "anime", "sort_order": 30},
    {"name": "Music", "slug": "music", "sort_order": 40},
    {"name": "Other", "slug": "other", "sort_order": 50},
]


def seed_default_categories(db: Session) -> None:
    category_count = db.scalar(select(func.count()).select_from(Category)) or 0
    if category_count > 0:
        return

    for item in DEFAULT_CATEGORIES:
        db.add(Category(**item))

    db.commit()
