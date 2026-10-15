"""SQLAlchemy ORM Models – Mapping to SQL Server tables (see SDD §3.2).

Column types follow the data dictionary:
- `Unicode(n)` / `UnicodeText` → NVARCHAR(n) / NVARCHAR(MAX) on SQL Server (Vietnamese text).
- `DateTime2` → DATETIME2 on SQL Server, timestamps are stored as naive UTC.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.mssql import DATETIME2, NVARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.utils import utc_now

DateTime2 = DateTime().with_variant(DATETIME2(), "mssql")
# NVARCHAR(MAX) on SQL Server (never the deprecated NTEXT)
LongUnicode = UnicodeText().with_variant(NVARCHAR(None), "mssql")


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime2, nullable=False, default=utc_now, server_default=func.now())


# ── Users ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("idx_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    full_name: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    role: Mapped[str] = mapped_column(Unicode(20), nullable=False, default="STUDENT", server_default="STUDENT")  # STUDENT | INSTRUCTOR | ADMIN
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime2, nullable=False, default=utc_now, onupdate=utc_now, server_default=func.now()
    )

    # Relationships
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="instructor", foreign_keys="Course.instructor_id")
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="user")
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship("QuizAttempt", back_populates="user")
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="instructor")


# ── Categories ────────────────────────────────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(Unicode(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    created_at: Mapped[datetime] = _created_at()

    # Relationships
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="category")


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
    created_at: Mapped[datetime] = _created_at()
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
    created_at: Mapped[datetime] = _created_at()

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
    created_at: Mapped[datetime] = _created_at()

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="lessons")
    # Progress records are removed together with the lesson (ORM-level cascade, avoids
    # SQL Server "multiple cascade paths" error that a DB-level cascade would cause).
    progress_records: Mapped[list["LessonProgress"]] = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan"
    )


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


# ── Questions ─────────────────────────────────────────────────────────────────
class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instructor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(LongUnicode, nullable=False)
    question_type: Mapped[str] = mapped_column(Unicode(20), nullable=False, default="SINGLE_CHOICE", server_default="SINGLE_CHOICE")  # SINGLE_CHOICE | MULTIPLE_CHOICE
    explanation: Mapped[str | None] = mapped_column(LongUnicode, nullable=True)
    created_at: Mapped[datetime] = _created_at()

    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", order_by="QuestionOption.order_index")
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship("QuizQuestion", back_populates="question")
    attempt_answers: Mapped[list["QuizAttemptAnswer"]] = relationship("QuizAttemptAnswer", back_populates="question")


# ── QuestionOptions ───────────────────────────────────────────────────────────
class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(LongUnicode, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="options")


# ── Quizzes ───────────────────────────────────────────────────────────────────
class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    chapter_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("chapters.id"), nullable=True)
    title: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    description: Mapped[str | None] = mapped_column(LongUnicode, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15, server_default=text("15"))
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default=text("3"))
    passing_score: Mapped[float] = mapped_column(Float, nullable=False, default=8.0, server_default=text("8.0"))
    created_at: Mapped[datetime] = _created_at()

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="quizzes")
    chapter: Mapped["Chapter | None"] = relationship("Chapter", back_populates="quizzes")
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")
    attempts: Mapped[list["QuizAttempt"]] = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


# ── QuizQuestions ─────────────────────────────────────────────────────────────
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (UniqueConstraint("quiz_id", "question_id", name="uq_quiz_question"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    point: Mapped[float] = mapped_column(Float, nullable=False, default=1.0, server_default=text("1.0"))

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="quiz_questions")
    question: Mapped["Question"] = relationship("Question", back_populates="quiz_questions")


# ── QuizAttempts ──────────────────────────────────────────────────────────────
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("idx_quiz_attempts_user", "quiz_id", "user_id", "attempt_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    started_at: Mapped[datetime] = mapped_column(DateTime2, nullable=False, default=utc_now, server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime2, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    status: Mapped[str] = mapped_column(Unicode(20), nullable=False, default="IN_PROGRESS", server_default="IN_PROGRESS")  # IN_PROGRESS | SUBMITTED | TIMEOUT

    # Relationships
    quiz:Mapped["Quiz"] = relationship("Quiz", back_populates="attempts")
    user: Mapped["User"] = relationship("User", back_populates="quiz_attempts")
    answers: Mapped[list["QuizAttemptAnswer"]] = relationship("QuizAttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")


# ── QuizAttemptAnswers ────────────────────────────────────────────────────────
class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option_ids: Mapped[str | None] = mapped_column(Unicode(255), nullable=True)  # JSON: "[1, 2]"

    # Relationships
    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="attempt_answers")
