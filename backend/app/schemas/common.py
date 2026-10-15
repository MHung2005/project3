"""Pydantic schemas shared by every module."""
import math
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel):
    """Standard response envelope (SDD §5.1)."""
    success: bool = True
    message: str = "Thao tác thành công"
    data: Any = None
    error: Optional[Any] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def build(cls, items: List[Any], total: int, page: int, limit: int) -> "PaginatedResponse[T]":
        pages = math.ceil(total / limit) if total > 0 else 1
        return cls(items=items, total=total, page=page, limit=limit, pages=pages)
