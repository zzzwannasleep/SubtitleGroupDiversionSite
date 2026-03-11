from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import mask_secret
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import AuthenticatedUserRead, UserRead
from app.services.auth_service import authenticate_user, create_access_token_for_user, register_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    try:
        user = register_user(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserRead(id=user.id, username=user.username, email=user.email, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db=db, identifier=payload.username, password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token_for_user(user))


@router.get("/me", response_model=AuthenticatedUserRead)
def me(current_user: User = Depends(get_current_user)) -> AuthenticatedUserRead:
    return AuthenticatedUserRead(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        status=current_user.status,
        avatar_url=current_user.avatar_url,
        tracker_credential=mask_secret(current_user.tracker_credential),
        rss_key=mask_secret(current_user.rss_key),
        created_at=current_user.created_at,
    )
