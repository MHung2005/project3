"""API Router – Authentication & personal profile."""
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from app.api.deps import CurrentUser, DBSession
from app.core.config import settings
from app.schemas.common import APIResponse
from app.schemas.user import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserBriefResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth" 


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path=REFRESH_COOKIE_PATH,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Đăng ký tài khoản học viên")
def register(data: UserRegisterRequest, db: DBSession):
    user = AuthService(db).register(data)
    return APIResponse(
        message="Đăng ký tài khoản thành công",
        data={"user_id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
    )


@router.post("/login", summary="Đăng nhập hệ thống")
def login(data: UserLoginRequest, response: Response, db: DBSession):
    result = AuthService(db).login(data.email, data.password)
    _set_refresh_cookie(response, result["refresh_token"])
    return APIResponse(
        message="Đăng nhập thành công",
        data={
            "access_token": result["access_token"],
            "token_type": "bearer",
            "user": UserBriefResponse.model_validate(result["user"]),
        },
    )


@router.post("/refresh", summary="Làm mới Access Token bằng Refresh Token (cookie)")
def refresh_token(
    db: DBSession,
    refresh_token: Optional[str] = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không tồn tại. Vui lòng đăng nhập lại.",
        )
    new_access_token = AuthService(db).refresh_access_token(refresh_token)
    return APIResponse(
        message="Làm mới token thành công",
        data={"access_token": new_access_token, "token_type": "bearer"},
    )


@router.post("/logout", summary="Đăng xuất")
def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
    return APIResponse(message="Đăng xuất thành công")


@router.get("/me", summary="Thông tin người dùng hiện tại")
def get_me(current_user: CurrentUser):
    return APIResponse(data=UserResponse.model_validate(current_user))


@router.put("/profile", summary="Cập nhật hồ sơ cá nhân")
def update_profile(data: UpdateProfileRequest, current_user: CurrentUser, db: DBSession):
    user = AuthService(db).update_profile(current_user, data)
    return APIResponse(message="Cập nhật hồ sơ thành công", data=UserResponse.model_validate(user))


@router.post("/change-password", summary="Đổi mật khẩu")
def change_password(data: ChangePasswordRequest, current_user: CurrentUser, db: DBSession):
    AuthService(db).change_password(current_user, data)
    return APIResponse(message="Đổi mật khẩu thành công")
