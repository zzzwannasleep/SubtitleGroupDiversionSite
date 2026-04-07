from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import generate_rss_key, mask_secret
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserProfileRead


router = APIRouter(prefix="/api/users", tags=["users"])


class UserProfileUpdateRequest(BaseModel):
    email: EmailStr
    avatar_url: str | None = Field(default=None, max_length=1024)
    bio: str | None = Field(default=None, max_length=2000)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("avatar_url", mode="before")
    @classmethod
    def normalize_avatar_url(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value

        trimmed_value = value.strip()
        if not trimmed_value:
            return None
        if not (trimmed_value.startswith("http://") or trimmed_value.startswith("https://")):
            raise ValueError("Avatar URL must start with http:// or https://")
        return trimmed_value


def _build_profile_response(user: User) -> UserProfileRead:
    stats = user.stats_cache
    return UserProfileRead(
        id=user.id,
        username=user.username,
        email=user.email,
        avatar_url=user.avatar_url,
        bio=user.bio,
        role=user.role,
        status=user.status,
        rss_key=user.rss_key,
        created_at=user.created_at,
        tracker_credential=mask_secret(user.tracker_credential),
        uploaded_bytes=stats.uploaded_bytes if stats else 0,
        downloaded_bytes=stats.downloaded_bytes if stats else 0,
        ratio=stats.ratio if stats else None,
    )


@router.get("/profile", response_model=UserProfileRead)
def get_profile(current_user: User = Depends(get_current_user)) -> UserProfileRead:
    return _build_profile_response(current_user)


@router.patch("/profile", response_model=UserProfileRead)
def update_profile(
    payload: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileRead:
    existing_user = db.query(User).filter(User.email == payload.email, User.id != current_user.id).first()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    current_user.email = payload.email
    current_user.avatar_url = payload.avatar_url.strip() if payload.avatar_url and payload.avatar_url.strip() else None
    current_user.bio = payload.bio.strip() if payload.bio and payload.bio.strip() else None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _build_profile_response(current_user)


@router.post("/profile/rss-key/rotate", response_model=UserProfileRead)
def rotate_profile_rss_key(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileRead:
    for _ in range(10):
        next_key = generate_rss_key()
        existing_user_id = db.scalar(select(User.id).where(User.rss_key == next_key))
        if existing_user_id is None:
            current_user.rss_key = next_key
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
            return _build_profile_response(current_user)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate a unique RSS key",
    )
