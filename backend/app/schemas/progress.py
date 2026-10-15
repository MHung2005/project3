"""Pydantic schemas – Enrollment & Progress."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.course import CourseResponse


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
    status: str
    progress_percentage: float
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MyCourseResponse(BaseModel):
    """An enrollment with its course – used for the student dashboard."""
    enrollment: EnrollmentResponse
    course: CourseResponse


class LessonProgressState(BaseModel):
    """Progress of one lesson for the current user (exists even when never opened)."""
    lesson_id: int
    is_completed: bool = False
    last_watched_second: int = 0
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SaveLessonPositionRequest(BaseModel):
    last_watched_second: int = Field(..., ge=0)


class CompleteLessonRequest(BaseModel):
    last_watched_second: int = Field(default=0, ge=0)


class CompleteLessonResponse(BaseModel):
    lesson_id: int
    is_completed: bool
    course_progress_percentage: float
    is_course_completed: bool


class QuizProgressState(BaseModel):
    quiz_id: int
    title: str
    chapter_id: Optional[int] = None
    attempts_used: int
    max_attempts: int
    best_score: Optional[float] = None
    is_passed: bool


class CourseProgressResponse(BaseModel):
    enrollment: EnrollmentResponse
    total_items: int
    completed_items: int
    total_lessons: int
    completed_lessons: int
    lessons: List[LessonProgressState]
    quizzes: List[QuizProgressState]


class StudentProgressInfo(BaseModel):
    user_id: int
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    enrolled_at: datetime
    progress_percentage: float
    completed_lessons: int
    total_lessons: int
    status: str
    completed_at: Optional[datetime] = None
