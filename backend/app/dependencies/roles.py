from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency

