"""ORM models – User accounts."""
from datetime import datetime

from sqlalchemy import Boolean, Index, Integer, Unicode, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utc_now
from app.db.base import Base
from app.models.types import DateTime2, created_at_column


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
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime2, nullable=False, default=utc_now, onupdate=utc_now, server_default=func.now()
    )

    # Relationships
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="instructor", foreign_keys="Course.instructor_id")
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="user")
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship("QuizAttempt", back_populates="user")
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="instructor")
