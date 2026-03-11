from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_rss_key,
    generate_tracker_credential,
    hash_password,
    verify_password,
)
from app.models.tracker_user_stats_cache import TrackerUserStatsCache
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest


def register_user(db: Session, payload: RegisterRequest) -> User:
    settings = get_settings()
    if not settings.allow_user_registration:
        raise ValueError("Registration is disabled")

    existing_user = db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first()
    if existing_user is not None:
        raise ValueError("Username or email already exists")

    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    role = UserRole.ADMIN if user_count == 0 else UserRole.USER

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
        tracker_credential=generate_tracker_credential(),
        rss_key=generate_rss_key(),
    )
    db.add(user)
    db.flush()

    db.add(TrackerUserStatsCache(user_id=user.id, uploaded_bytes=0, downloaded_bytes=0))
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User | None:
    user = db.query(User).filter((User.username == identifier) | (User.email == identifier)).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(UTC)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_access_token_for_user(user: User) -> str:
    return create_access_token(str(user.id))

