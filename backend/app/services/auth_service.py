"""Service – Authentication & User management business logic."""
import logging
from typing import Optional

from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserListResponse,
    UserRegisterRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)


def _token_payload(user: User) -> dict:
    return {"sub": str(user.id), "email": user.email, "role": user.role}


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, data: UserRegisterRequest) -> User:
        if self.repo.get_by_email(data.email):
            raise BadRequestError("Email đã được sử dụng. Vui lòng chọn email khác.")
        return self.repo.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role="STUDENT",
        )

    def login(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Email hoặc mật khẩu không chính xác.")
        if not user.is_active:
            raise UnauthorizedError("Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.")
        payload = _token_payload(user)
        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token(payload),
            "user": user,
        }

    def update_profile(self, user: User, data: UpdateProfileRequest) -> User:
        return self.repo.update(user, **data.model_dump(exclude_none=True))

    def change_password(self, user: User, data: ChangePasswordRequest) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise BadRequestError("Mật khẩu hiện tại không chính xác.")
        if data.current_password == data.new_password:
            raise BadRequestError("Mật khẩu mới phải khác mật khẩu hiện tại.")
        self.repo.update(user, hashed_password=hash_password(data.new_password))

    def refresh_access_token(self, refresh_token: str) -> str:
        invalid = UnauthorizedError("Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.")
        try:
            payload = decode_token(refresh_token)
            user_id = int(payload["sub"])
        except (JWTError, KeyError, ValueError):
            raise invalid
        if payload.get("type") != "refresh":
            raise invalid
        user = self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("Tài khoản không hợp lệ hoặc đã bị khóa.")
        # Role may have changed since login – always issue the token from current DB state
        return create_access_token(_token_payload(user))

    def authenticate_access_token(self, token: str) -> User:
        """Return the active user an access token belongs to, raising 401 on any failure."""
        invalid = UnauthorizedError("Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.")
        try:
            payload = decode_token(token)
            user_id = int(payload["sub"])
        except (JWTError, KeyError, ValueError):
            raise invalid
        if payload.get("type") != "access":
            raise invalid
        user = self.repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise invalid
        return user

    def update_avatar(self, user: User, avatar_url: str) -> User:
        return self.repo.update(user, avatar_url=avatar_url)


class AdminUserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_users(
        self,
        page: int,
        limit: int,
        role: Optional[str],
        search: Optional[str],
        is_active: Optional[bool] = None,
    ) -> UserListResponse:
        items, total = self.repo.get_all_paginated(page, limit, role, search, is_active)
        return UserListResponse.build(
            items=[UserResponse.model_validate(u) for u in items], total=total, page=page, limit=limit
        )

    def get_user(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("Người dùng không tồn tại.")
        return user

    def update_status(self, user_id: int, is_active: bool, current_admin: User) -> User:
        user = self.get_user(user_id)
        if user.id == current_admin.id and not is_active:
            raise BadRequestError("Bạn không thể tự khóa tài khoản của mình.")
        return self.repo.update(user, is_active=is_active)

    def update_role(self, user_id: int, role: str, current_admin: User) -> User:
        user = self.get_user(user_id)
        if user.id == current_admin.id and role != "ADMIN":
            raise BadRequestError("Bạn không thể tự hạ quyền quản trị của chính mình.")
        return self.repo.update(user, role=role)


def seed_first_admin(db: Session) -> None:
    """Create the initial ADMIN account from env settings if it does not exist yet."""
    if not settings.FIRST_ADMIN_EMAIL or not settings.FIRST_ADMIN_PASSWORD:
        return
    repo = UserRepository(db)
    if repo.get_by_email(settings.FIRST_ADMIN_EMAIL):
        return
    repo.create(
        email=settings.FIRST_ADMIN_EMAIL,
        hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
        full_name=settings.FIRST_ADMIN_FULL_NAME,
        role="ADMIN",
    )
    logger.info("Seeded initial admin account %s", settings.FIRST_ADMIN_EMAIL)
