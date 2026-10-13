"""FastAPI Dependencies – DB session, JWT authentication, RBAC role guards."""
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.models import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)

# ── Type aliases ──────────────────────────────────────────────────────────────
DBSession = Annotated[Session, Depends(get_db)]


def _get_user_from_token(token: str, db: Session) -> User:
    """Decode JWT and load user from DB, raising 401 on any failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: int = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise credentials_exception

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DBSession,
) -> User:
    """Dependency: returns the currently authenticated user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa xác thực. Vui lòng đăng nhập.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _get_user_from_token(credentials.credentials, db)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str):
    """Factory that returns a dependency requiring one of the given roles."""
    def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tính năng này yêu cầu quyền: {', '.join(roles)}.",
            )
        return current_user
    return _check


# Convenience role guards
RequireStudent = Annotated[User, Depends(require_role("STUDENT", "INSTRUCTOR", "ADMIN"))]
RequireInstructor = Annotated[User, Depends(require_role("INSTRUCTOR", "ADMIN"))]
RequireAdmin = Annotated[User, Depends(require_role("ADMIN"))]
