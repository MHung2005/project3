"""API Router – Admin user management & RBAC (SDD §5.2)."""
from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import DBSession, RequireAdmin
from app.schemas.common import APIResponse
from app.schemas.user import UpdateUserRoleRequest, UpdateUserStatusRequest, UserResponse
from app.services.auth_service import AdminUserService

router = APIRouter(prefix="/admin/users")


@router.get("", summary="[Admin] Danh sách người dùng (phân trang, lọc theo vai trò)")
def admin_get_users(
    db: DBSession,
    current_user: RequireAdmin,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    role: Optional[str] = Query(default=None, pattern="^(STUDENT|INSTRUCTOR|ADMIN)$"),
    search: Optional[str] = Query(default=None, max_length=100),
    is_active: Optional[bool] = Query(default=None),
):
    result = AdminUserService(db).get_users(page=page, limit=limit, role=role, search=search, is_active=is_active)
    return APIResponse(data=result)


@router.get("/{user_id}", summary="[Admin] Chi tiết người dùng")
def admin_get_user(user_id: int, db: DBSession, current_user: RequireAdmin):
    user = AdminUserService(db).get_user(user_id)
    return APIResponse(data=UserResponse.model_validate(user))


@router.patch("/{user_id}/status", summary="[Admin] Khóa/Mở khóa tài khoản")
def admin_update_status(user_id: int, data: UpdateUserStatusRequest, db: DBSession, current_user: RequireAdmin):
    user = AdminUserService(db).update_status(user_id, data.is_active, current_user)
    return APIResponse(
        message=f"Tài khoản đã được {'mở khóa' if data.is_active else 'khóa'}.",
        data=UserResponse.model_validate(user),
    )


@router.patch("/{user_id}/role", summary="[Admin] Thay đổi quyền hạn")
def admin_update_role(user_id: int, data: UpdateUserRoleRequest, db: DBSession, current_user: RequireAdmin):
    user = AdminUserService(db).update_role(user_id, data.role, current_user)
    return APIResponse(
        message=f"Đã thay đổi quyền hạn thành {data.role}.",
        data=UserResponse.model_validate(user),
    )
