"""Pydantic schemas – Categories."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: Optional[str] = Field(None, max_length=500)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = Field(None, min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: Optional[str] = Field(None, max_length=500)


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryBriefResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}
