"""Repository – Enrollment & LessonProgress data access."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Chapter, Enrollment, Lesson, LessonProgress


class EnrollmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_course(self, user_id: int, course_id: int) -> Optional[Enrollment]:
        return (
            self.db.query(Enrollment)
            .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
            .first()
        )

    def get_by_id(self, enrollment_id: int) -> Optional[Enrollment]:
        return self.db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()

    def get_by_course(self, course_id: int) -> list[Enrollment]:
        return self.db.query(Enrollment).filter(Enrollment.course_id == course_id).all()

    def get_by_user(self, user_id: int) -> list[Enrollment]:
        return self.db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

    def create(self, user_id: int, course_id: int) -> Enrollment:
        enrollment = Enrollment(user_id=user_id, course_id=course_id)
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment

    def update(self, enrollment: Enrollment, **kwargs) -> Enrollment:
        for key, value in kwargs.items():
            if hasattr(enrollment, key):
                setattr(enrollment, key, value)
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment


class LessonProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_enrollment_and_lesson(
        self, enrollment_id: int, lesson_id: int
    ) -> Optional[LessonProgress]:
        return (
            self.db.query(LessonProgress)
            .filter(
                LessonProgress.enrollment_id == enrollment_id,
                LessonProgress.lesson_id == lesson_id,
            )
            .first()
        )

    def get_all_for_enrollment(self, enrollment_id: int) -> list[LessonProgress]:
        return (
            self.db.query(LessonProgress)
            .filter(LessonProgress.enrollment_id == enrollment_id)
            .all()
        )

    def upsert(
        self,
        enrollment_id: int,
        lesson_id: int,
        last_watched_second: int,
        is_completed: bool,
    ) -> LessonProgress:
        progress = self.get_by_enrollment_and_lesson(enrollment_id, lesson_id)
        if progress is None:
            progress = LessonProgress(
                enrollment_id=enrollment_id,
                lesson_id=lesson_id,
                last_watched_second=last_watched_second,
                is_completed=is_completed,
                completed_at=datetime.now(timezone.utc) if is_completed else None,
            )
            self.db.add(progress)
        else:
            progress.last_watched_second = last_watched_second
            if is_completed and not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(progress)
        return progress

    def count_completed(self, enrollment_id: int) -> int:
        return (
            self.db.query(LessonProgress)
            .filter(
                LessonProgress.enrollment_id == enrollment_id,
                LessonProgress.is_completed == True,
            )
            .count()
        )

    def count_total_lessons_in_course(self, course_id: int) -> int:
        return (
            self.db.query(Lesson)
            .join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(Chapter.course_id == course_id)
            .count()
        )
