"""ORM models – Course content: courses, chapters and lessons."""
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Unicode, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utc_now
from app.db.base import Base
from app.models.types import DateTime2, LongUnicode, created_at_column


# ── Courses ───────────────────────────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        Index("idx_courses_status_cat", "status", "category_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instructor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    title: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    description: Mapped[str | None] = mapped_column(LongUnicode, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    status: Mapped[str] = mapped_column(Unicode(20), nullable=False, default="DRAFT", server_default="DRAFT")  # DRAFT | PENDING | PUBLISHED | REJECTED
    rejection_reason: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime2, nullable=False, default=utc_now, onupdate=utc_now, server_default=func.now()
    )

    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="courses", foreign_keys=[instructor_id])
    category: Mapped["Category"] = relationship("Category", back_populates="courses")
    chapters: Mapped[list["Chapter"]] = relationship("Chapter", back_populates="course", cascade="all, delete-orphan", order_by="Chapter.order_index")
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="course")
    quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")


# ── Chapters ──────────────────────────────────────────────────────────────────
class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    created_at: Mapped[datetime] = created_at_column()

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="chapters")
    lessons: Mapped[list["Lesson"]] = relationship("Lesson", back_populates="chapter", cascade="all, delete-orphan", order_by="Lesson.order_index")
    quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="chapter")


# ── Lessons ───────────────────────────────────────────────────────────────────
class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    lesson_type: Mapped[str] = mapped_column(Unicode(20), nullable=False)  # VIDEO | DOCUMENT
    video_url: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    document_url: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    is_free_preview: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at: Mapped[datetime] = created_at_column()

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="lessons")
    # Progress records are removed together with the lesson (ORM-level cascade, avoids
    # SQL Server "multiple cascade paths" error that a DB-level cascade would cause).
    progress_records: Mapped[list["LessonProgress"]] = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan"
    )
