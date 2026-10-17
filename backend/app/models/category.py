"""ORM models – Course categories."""
from datetime import datetime

from sqlalchemy import Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import created_at_column


# ── Categories ────────────────────────────────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(Unicode(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    created_at: Mapped[datetime] = created_at_column()

    # Relationships
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="category")
