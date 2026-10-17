"""ORM models – Question bank, quizzes and quiz attempts."""
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, Unicode, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utc_now
from app.db.base import Base
from app.models.types import DateTime2, LongUnicode, created_at_column


# ── Questions ─────────────────────────────────────────────────────────────────
class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instructor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(LongUnicode, nullable=False)
    question_type: Mapped[str] = mapped_column(Unicode(20), nullable=False, default="SINGLE_CHOICE", server_default="SINGLE_CHOICE")  # SINGLE_CHOICE | MULTIPLE_CHOICE
    explanation: Mapped[str | None] = mapped_column(LongUnicode, nullable=True)
    created_at: Mapped[datetime] = created_at_column()

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
    created_at: Mapped[datetime] = created_at_column()

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
