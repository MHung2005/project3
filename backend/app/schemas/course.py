"""Pydantic schemas – Courses, Chapters, Lessons."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserBriefResponse


# ── Lesson Schemas ────────────────────────────────────────────────────────────
class LessonCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    lesson_type: str = Field(..., pattern="^(VIDEO|DOCUMENT)$")
    video_url: Optional[str] = None
    document_url: Optional[str] = None
    duration_seconds: int = Field(default=0, ge=0)
    order_index: int = Field(default=1, ge=1)
    is_free_preview: bool = False


class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    lesson_type: Optional[str] = Field(None, pattern="^(VIDEO|DOCUMENT)$")
    video_url: Optional[str] = None
    document_url: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    order_index: Optional[int] = Field(None, ge=1)
    is_free_preview: Optional[bool] = None


class LessonResponse(BaseModel):
    id: int
    chapter_id: int
    title: str
    lesson_type: str
    video_url: Optional[str] = None
    document_url: Optional[str] = None
    duration_seconds: int
    order_index: int
    is_free_preview: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Chapter Schemas ───────────────────────────────────────────────────────────
class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    order_index: int = Field(default=1, ge=1)


class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    order_index: Optional[int] = Field(None, ge=1)


class ChapterResponse(BaseModel):
    id: int
    course_id: int
    title: str
    order_index: int
    created_at: datetime
    lessons: List[LessonResponse] = []

    model_config = {"from_attributes": True}


class ChapterBriefResponse(BaseModel):
    id: int
    course_id: int
    title: str
    order_index: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Course Schemas ────────────────────────────────────────────────────────────
class CourseCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    category_id: int = Field(..., gt=0)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    category_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None


class CourseResponse(BaseModel):
    id: int
    instructor_id: int
    category_id: int
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CourseDetailResponse(CourseResponse):
    """Course with chapters + lessons + instructor info."""
    instructor: Optional[UserBriefResponse] = None
    chapters: List[ChapterResponse] = []


class CourseListResponse(BaseModel):
    items: List[CourseResponse]
    total: int
    page: int
    limit: int
    pages: int


class RejectCourseRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


class EnrollStudentRequest(BaseModel):
    student_email: str
