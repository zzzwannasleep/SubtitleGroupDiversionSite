from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import mask_secret
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import AuthenticatedUserRead, UserRead
from app.services.auth_service import authenticate_user, create_access_token_for_user, register_user
from app.services.rate_limit_service import RateLimitExceeded, auth_rate_limiter, get_request_ip


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _enforce_auth_rate_limit(request: Request, action: str) -> None:
    settings = get_settings()
    if not settings.auth_rate_limit_enabled:
        return

    limit = (
        settings.auth_login_rate_limit_attempts
        if action == "login"
        else settings.auth_register_rate_limit_attempts
    )
    key = f"auth:{action}:{get_request_ip(request)}"

    try:
        auth_rate_limiter.hit(key, limit=limit, window_seconds=settings.auth_rate_limit_window_seconds)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many {action} attempts. Try again later.",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    _enforce_auth_rate_limit(request, "register")
    try:
        user = register_user(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserRead(id=user.id, username=user.username, email=user.email, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    _enforce_auth_rate_limit(request, "login")
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
