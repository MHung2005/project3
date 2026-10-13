"""Service – Enrollment & Progress business logic."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Enrollment
from app.repositories.course_repository import CourseRepository
from app.repositories.progress_repository import EnrollmentRepository, LessonProgressRepository
from app.repositories.user_repository import UserRepository
from app.schemas.progress import (
    CompleteLessonRequest,
    CompleteLessonResponse,
    CourseProgressResponse,
)


class EnrollmentService:
    def __init__(self, db: Session):
        self.enrollment_repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)
        self.progress_repo = LessonProgressRepository(db)

    def enroll(self, user_id: int, course_id: int) -> Enrollment:
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khóa học không tồn tại.")
        if course.status != "PUBLISHED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chỉ có thể đăng ký các khóa học đã xuất bản.",
            )
        existing = self.enrollment_repo.get_by_user_and_course(user_id, course_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn đã đăng ký khóa học này rồi.",
            )
        return self.enrollment_repo.create(user_id=user_id, course_id=course_id)

    def get_course_progress(self, user_id: int, course_id: int) -> CourseProgressResponse:
        enrollment = self.enrollment_repo.get_by_user_and_course(user_id, course_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn chưa đăng ký khóa học này.",
            )
        lesson_progress = self.progress_repo.get_all_for_enrollment(enrollment.id)
        return CourseProgressResponse(enrollment=enrollment, lesson_progress=lesson_progress)

    def complete_lesson(
        self, user_id: int, lesson_id: int, data: CompleteLessonRequest
    ) -> CompleteLessonResponse:
        from app.repositories.course_repository import LessonRepository, ChapterRepository
        lesson_repo = LessonRepository(self.enrollment_repo.db)
        chapter_repo = ChapterRepository(self.enrollment_repo.db)

        lesson = lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bài học không tồn tại.")

        chapter = chapter_repo.get_by_id(lesson.chapter_id)
        enrollment = self.enrollment_repo.get_by_user_and_course(user_id, chapter.course_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn chưa đăng ký khóa học chứa bài học này.",
            )

        # Mark lesson as completed
        self.progress_repo.upsert(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            last_watched_second=data.last_watched_second,
            is_completed=True,
        )

        # Recalculate overall course progress
        completed_count = self.progress_repo.count_completed(enrollment.id)
        total_count = self.progress_repo.count_total_lessons_in_course(chapter.course_id)
        progress_pct = (completed_count / total_count * 100) if total_count > 0 else 0.0

        is_course_completed = progress_pct >= 100.0
        update_kwargs: dict = {"progress_percentage": progress_pct}
        if is_course_completed and enrollment.status != "COMPLETED":
            update_kwargs["status"] = "COMPLETED"
            update_kwargs["completed_at"] = datetime.now(timezone.utc)

        self.enrollment_repo.update(enrollment, **update_kwargs)

        return CompleteLessonResponse(
            lesson_id=lesson_id,
            is_completed=True,
            course_progress_percentage=round(progress_pct, 2),
            is_course_completed=is_course_completed,
        )
