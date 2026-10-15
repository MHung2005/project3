"""Pydantic schemas for Request/Response validation – Auth & Users."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import PaginatedResponse


def _validate_password_strength(v: str) -> str:
    if not any(c.isupper() for c in v):
        raise ValueError("Mật khẩu phải có ít nhất 1 chữ hoa")
    if not any(c.isdigit() for c in v):
        raise ValueError("Mật khẩu phải có ít nhất 1 chữ số")
    return v


# ── User Schemas ──────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)


class UserRegisterRequest(UserBase):
    password: str = Field(..., min_length=6, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBriefResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class InstructorBriefResponse(BaseModel):
    """Public instructor info shown on course pages (no email)."""
    id: int
    full_name: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    avatar_url: Optional[str] = Field(None, max_length=500)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=72)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(STUDENT|INSTRUCTOR|ADMIN)$")


UserListResponse = PaginatedResponse[UserResponse]
