from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserStatus


def _read_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    return authorization[len(prefix) :].strip()


def get_current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User | None:
    token = _read_bearer_token(authorization)
    if token is None:
        return None
    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        return None
    user = db.get(User, int(subject))
    if user is None or user.status != UserStatus.ACTIVE:
        return None
    return user


def get_current_user(current_user: User | None = Depends(get_current_user_optional)) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user
