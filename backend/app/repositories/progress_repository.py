"""Repository – Enrollment & LessonProgress data access."""
from typing import Optional

from sqlalchemy import func, true
from sqlalchemy.orm import Session, selectinload

from app.core.utils import utc_now
from app.models.models import Course, Enrollment, LessonProgress


class EnrollmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_course(self, user_id: int, course_id: int) -> Optional[Enrollment]:
        return (
            self.db.query(Enrollment)
            .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
            .first()
        )

    def get_by_course(self, course_id: int) -> list[Enrollment]:
        return (
            self.db.query(Enrollment)
            .options(selectinload(Enrollment.user))
            .filter(Enrollment.course_id == course_id)
            .order_by(Enrollment.enrolled_at.desc())
            .all()
        )

    def get_by_user(self, user_id: int, status: Optional[str] = None) -> list[Enrollment]:
        query = (
            self.db.query(Enrollment)
            .options(
                selectinload(Enrollment.course).selectinload(Course.instructor),
                selectinload(Enrollment.course).selectinload(Course.category),
            )
            .filter(Enrollment.user_id == user_id)
        )
        if status:
            query = query.filter(Enrollment.status == status)
        return query.order_by(Enrollment.enrolled_at.desc()).all()

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
        """Save the watch position; completion is sticky (never reverts to False)."""
        progress = self.get_by_enrollment_and_lesson(enrollment_id, lesson_id)
        if progress is None:
            progress = LessonProgress(
                enrollment_id=enrollment_id,
                lesson_id=lesson_id,
                last_watched_second=last_watched_second,
                is_completed=is_completed,
                completed_at=utc_now() if is_completed else None,
            )
            self.db.add(progress)
        else:
            progress.last_watched_second = last_watched_second
            if is_completed and not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = utc_now()
        self.db.commit()
        self.db.refresh(progress)
        return progress

    def count_completed(self, enrollment_id: int) -> int:
        return (
            self.db.query(LessonProgress)
            .filter(
                LessonProgress.enrollment_id == enrollment_id,
                LessonProgress.is_completed == true(),
            )
            .count()
        )

    def count_completed_by_enrollments(self, enrollment_ids: list[int]) -> dict[int, int]:
        """Return {enrollment_id: completed_lesson_count} in one query."""
        if not enrollment_ids:
            return {}
        rows = (
            self.db.query(LessonProgress.enrollment_id, func.count(LessonProgress.id))
            .filter(
                LessonProgress.enrollment_id.in_(enrollment_ids),
                LessonProgress.is_completed == true(),
            )
            .group_by(LessonProgress.enrollment_id)
            .all()
        )
        return dict(rows)
