"""API Router – Authentication & Users."""
from typing import Annotated, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, DBSession, RequireAdmin, RequireInstructor
from app.schemas.user import (
    APIResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AdminUserService, AuthService
from app.core.config import settings

router = APIRouter()


# ── Registration ──────────────────────────────────────────────────────────────
@router.post("/auth/register", status_code=status.HTTP_201_CREATED, summary="Đăng ký tài khoản")
def register(data: UserRegisterRequest, db: DBSession):
    svc = AuthService(db)
    user = svc.register(data)
    return APIResponse(
        message="Đăng ký tài khoản thành công",
        data={"user_id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
    )


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/auth/login", summary="Đăng nhập hệ thống")
def login(data: UserLoginRequest, response: Response, db: DBSession):
    svc = AuthService(db)
    result = svc.login(data.email, data.password)
    # Set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        samesite="lax",
        secure=False,  # Set True in production with HTTPS
    )
    user = result["user"]
    return APIResponse(
        message="Đăng nhập thành công",
        data={
            "access_token": result["access_token"],
            "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
        },
    )


# ── Refresh Token ─────────────────────────────────────────────────────────────
@router.post("/auth/refresh", summary="Làm mới Access Token")
def refresh_token(
    db: DBSession,
    refresh_token: Optional[str] = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không tồn tại. Vui lòng đăng nhập lại.",
        )
    svc = AuthService(db)
    new_access_token = svc.refresh_access_token(refresh_token)
    return APIResponse(
        message="Làm mới token thành công",
        data={"access_token": new_access_token, "token_type": "bearer"},
    )


# ── Logout ────────────────────────────────────────────────────────────────────
@router.post("/auth/logout", summary="Đăng xuất")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return APIResponse(message="Đăng xuất thành công")


# ── Me ────────────────────────────────────────────────────────────────────────
@router.get("/auth/me", summary="Thông tin người dùng hiện tại")
def get_me(current_user: CurrentUser, db: DBSession):
    svc = AuthService(db)
    user = svc.get_me(current_user.id)
    return APIResponse(data=UserResponse.model_validate(user))


# ── Update Profile ────────────────────────────────────────────────────────────
@router.put("/auth/profile", summary="Cập nhật hồ sơ cá nhân")
def update_profile(data: UpdateProfileRequest, current_user: CurrentUser, db: DBSession):
    svc = AuthService(db)
    user = svc.update_profile(current_user.id, data)
    return APIResponse(message="Cập nhật hồ sơ thành công", data=UserResponse.model_validate(user))


# ── Change Password ───────────────────────────────────────────────────────────
@router.post("/auth/change-password", summary="Đổi mật khẩu")
def change_password(data: ChangePasswordRequest, current_user: CurrentUser, db: DBSession):
    svc = AuthService(db)
    svc.change_password(current_user.id, data)
    return APIResponse(message="Đổi mật khẩu thành công")


# ── Admin: User List ──────────────────────────────────────────────────────────
@router.get("/admin/users", summary="[Admin] Danh sách người dùng")
def admin_get_users(
    db: DBSession,
    current_user: RequireAdmin,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    role: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
):
    svc = AdminUserService(db)
    result = svc.get_users(page=page, limit=limit, role=role, search=search)
    return APIResponse(data=result)


# ── Admin: Update Status ──────────────────────────────────────────────────────
@router.patch("/admin/users/{user_id}/status", summary="[Admin] Khóa/Mở khóa tài khoản")
def admin_update_status(user_id: int, data: UpdateUserStatusRequest, db: DBSession, current_user: RequireAdmin):
    svc = AdminUserService(db)
    user = svc.update_status(user_id, data.is_active)
    return APIResponse(
        message=f"Tài khoản đã được {'mở khóa' if data.is_active else 'khóa'}.",
        data=UserResponse.model_validate(user),
    )


# ── Admin: Update Role ────────────────────────────────────────────────────────
@router.patch("/admin/users/{user_id}/role", summary="[Admin] Thay đổi quyền hạn")
def admin_update_role(user_id: int, data: UpdateUserRoleRequest, db: DBSession, current_user: RequireAdmin):
    svc = AdminUserService(db)
    user = svc.update_role(user_id, data.role)
    return APIResponse(
        message=f"Đã thay đổi quyền hạn thành {data.role}.",
        data=UserResponse.model_validate(user),
    )
