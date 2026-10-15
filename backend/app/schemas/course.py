"""Pydantic schemas – Courses, Chapters, Lessons."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, computed_field, model_validator

from app.core.utils import extract_youtube_id
from app.schemas.category import CategoryBriefResponse
from app.schemas.common import PaginatedResponse
from app.schemas.user import InstructorBriefResponse


def validate_lesson_content(lesson_type: str, video_url: Optional[str], document_url: Optional[str]) -> None:
    """Business rule: VIDEO lessons need a YouTube URL, DOCUMENT lessons need a file URL."""
    if lesson_type == "VIDEO":
        if not video_url:
            raise ValueError("Bài học dạng VIDEO bắt buộc phải có video_url.")
        if extract_youtube_id(video_url) is None:
            raise ValueError("video_url phải là đường dẫn YouTube hợp lệ.")
    elif lesson_type == "DOCUMENT" and not document_url:
        raise ValueError("Bài học dạng DOCUMENT bắt buộc phải có document_url.")


# ── Lesson Schemas ────────────────────────────────────────────────────────────
class LessonCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    lesson_type: str = Field(..., pattern="^(VIDEO|DOCUMENT)$")
    video_url: Optional[str] = Field(None, max_length=500)
    document_url: Optional[str] = Field(None, max_length=500)
    duration_seconds: int = Field(default=0, ge=0)
    order_index: Optional[int] = Field(None, ge=1, description="Bỏ trống để tự động xếp cuối chương")
    is_free_preview: bool = False

    @model_validator(mode="after")
    def check_content(self) -> "LessonCreate":
        validate_lesson_content(self.lesson_type, self.video_url, self.document_url)
        return self


class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    lesson_type: Optional[str] = Field(None, pattern="^(VIDEO|DOCUMENT)$")
    video_url: Optional[str] = Field(None, max_length=500)
    document_url: Optional[str] = Field(None, max_length=500)
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
    # True when content URLs are hidden because the viewer is not enrolled
    is_locked: bool = False

    model_config = {"from_attributes": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def youtube_video_id(self) -> Optional[str]:
        return extract_youtube_id(self.video_url)


# ── Chapter Schemas ───────────────────────────────────────────────────────────
class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    order_index: Optional[int] = Field(None, ge=1, description="Bỏ trống để tự động xếp cuối khóa học")


class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    order_index: Optional[int] = Field(None, ge=1)


class ChapterBriefResponse(BaseModel):
    id: int
    course_id: int
    title: str
    order_index: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChapterResponse(ChapterBriefResponse):
    lessons: List[LessonResponse] = []


# ── Course Schemas ────────────────────────────────────────────────────────────
class CourseCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    category_id: int = Field(..., gt=0)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = Field(None, max_length=500)


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    category_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = Field(None, max_length=500)


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
    instructor: Optional[InstructorBriefResponse] = None
    category: Optional[CategoryBriefResponse] = None

    model_config = {"from_attributes": True}


class QuizBriefResponse(BaseModel):
    id: int
    chapter_id: Optional[int] = None
    title: str
    duration_minutes: int
    max_attempts: int
    passing_score: float

    model_config = {"from_attributes": True}


class CourseDetailResponse(CourseResponse):
    """Course with chapters + lessons + quizzes + instructor info."""
    chapters: List[ChapterResponse] = []
    quizzes: List[QuizBriefResponse] = []
    total_lessons: int = 0
    total_duration_seconds: int = 0
    enrollment_count: int = 0
    is_enrolled: bool = False


CourseListResponse = PaginatedResponse[CourseResponse]


class RejectCourseRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


class EnrollStudentRequest(BaseModel):
    student_email: EmailStr
