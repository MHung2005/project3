from typing import Annotated, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models import User
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


DBSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DBSession,
) -> User:
    """Dependency: returns the currently authenticated user."""
    if credentials is None:
        raise UnauthorizedError("Chưa xác thực. Vui lòng đăng nhập.")
    return AuthService(db).authenticate_access_token(credentials.credentials)


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DBSession,
) -> Optional[User]:
    """Dependency for public endpoints that personalise the response when a valid token is sent."""
    if credentials is None:
        return None
    try:
        return AuthService(db).authenticate_access_token(credentials.credentials)
    except UnauthorizedError:
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]


def require_role(*roles: str):
    """Factory that returns a dependency requiring one of the given roles."""
    def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(f"Tính năng này yêu cầu quyền: {', '.join(roles)}.")
        return current_user
    return _check


# Convenience role guards
RequireStudent = Annotated[User, Depends(require_role("STUDENT", "INSTRUCTOR", "ADMIN"))]
RequireInstructor = Annotated[User, Depends(require_role("INSTRUCTOR", "ADMIN"))]
RequireAdmin = Annotated[User, Depends(require_role("ADMIN"))]
