"""Service – Authentication & User management business logic."""
import math
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserListResponse,
    UserRegisterRequest,
)


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, data: UserRegisterRequest) -> User:
        if self.repo.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email đã được sử dụng. Vui lòng chọn email khác.",
            )
        hashed = hash_password(data.password)
        return self.repo.create(
            email=data.email,
            hashed_password=hashed,
            full_name=data.full_name,
            role="STUDENT",
        )

    def login(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không chính xác.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.",
            )
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        }

    def get_me(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")
        return user

    def update_profile(self, user_id: int, data: UpdateProfileRequest) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")
        update_data = data.model_dump(exclude_none=True)
        return self.repo.update(user, **update_data)

    def change_password(self, user_id: int, data: ChangePasswordRequest) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không chính xác.",
            )
        self.repo.update(user, hashed_password=hash_password(data.new_password))

    def refresh_access_token(self, refresh_token: str) -> str:
        from jose import JWTError
        from app.core.security import decode_token
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ.")
            user_id = int(payload["sub"])
            user = self.repo.get_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không hợp lệ.")
            token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
            return create_access_token(token_data)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token không hợp lệ hoặc đã hết hạn.")


class AdminUserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_users(self, page: int, limit: int, role: Optional[str], search: Optional[str]) -> UserListResponse:
        items, total = self.repo.get_all_paginated(page, limit, role, search)
        pages = math.ceil(total / limit) if total > 0 else 1
        return UserListResponse(items=items, total=total, page=page, limit=limit, pages=pages)

    def update_status(self, user_id: int, is_active: bool) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")
        return self.repo.update(user, is_active=is_active)

    def update_role(self, user_id: int, role: str) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")
        return self.repo.update(user, role=role)
