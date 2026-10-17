"""ORM models – Enrollments and per-lesson learning progress."""
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, Unicode, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utc_now
from app.db.base import Base
from app.models.types import DateTime2


# ── Enrollments ───────────────────────────────────────────────────────────────
class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        Index("idx_enrollment_user_course", "user_id", "course_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime2, nullable=False, default=utc_now, server_default=func.now())
    status: Mapped[str] = mapped_column(Unicode(20), nullable=False, default="IN_PROGRESS", server_default="IN_PROGRESS")  # IN_PROGRESS | COMPLETED
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default=text("0"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime2, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    lesson_progress: Mapped[list["LessonProgress"]] = relationship("LessonProgress", back_populates="enrollment", cascade="all, delete-orphan")


# ── LessonProgress ────────────────────────────────────────────────────────────
class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        Index("idx_lesson_progress_lookup", "enrollment_id", "lesson_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id"), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    last_watched_second: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime2, nullable=True)

    # Relationships
    enrollment: Mapped["Enrollment"] = relationship("Enrollment", back_populates="lesson_progress")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="progress_records")
