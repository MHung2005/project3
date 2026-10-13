"""Pydantic schemas – Enrollment & Progress."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
    status: str
    progress_percentage: float
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LessonProgressResponse(BaseModel):
    id: int
    enrollment_id: int
    lesson_id: int
    is_completed: bool
    last_watched_second: int
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CompleteLessonRequest(BaseModel):
    last_watched_second: int = 0


class CompleteLessonResponse(BaseModel):
    lesson_id: int
    is_completed: bool
    course_progress_percentage: float
    is_course_completed: bool


class CourseProgressResponse(BaseModel):
    enrollment: EnrollmentResponse
    lesson_progress: List[LessonProgressResponse]


class StudentProgressInfo(BaseModel):
    user_id: int
    email: str
    full_name: str
    enrolled_at: datetime
    progress_percentage: float
    status: str
    completed_at: Optional[datetime] = None
