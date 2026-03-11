from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import mask_secret
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserProfileRead


router = APIRouter(prefix="/api/users", tags=["users"])


class UserProfileUpdateRequest(BaseModel):
    email: EmailStr
    avatar_url: str | None = Field(default=None, max_length=1024)
    bio: str | None = Field(default=None, max_length=2000)


@router.get("/profile", response_model=UserProfileRead)
def get_profile(current_user: User = Depends(get_current_user)) -> UserProfileRead:
    stats = current_user.stats_cache
    return UserProfileRead(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        role=current_user.role,
        status=current_user.status,
        rss_key=current_user.rss_key,
        created_at=current_user.created_at,
        tracker_credential=mask_secret(current_user.tracker_credential),
        uploaded_bytes=stats.uploaded_bytes if stats else 0,
        downloaded_bytes=stats.downloaded_bytes if stats else 0,
        ratio=stats.ratio if stats else None,
    )


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
    return get_profile(current_user)
