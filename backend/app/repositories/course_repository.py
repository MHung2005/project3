"""Repository – Course, Chapter, Lesson data access."""
import math
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.models.models import Chapter, Course, Lesson


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Course ────────────────────────────────────────────────────────────────
    def get_by_id(self, course_id: int) -> Optional[Course]:
        return self.db.query(Course).filter(Course.id == course_id).first()

    def get_detail(self, course_id: int) -> Optional[Course]:
        return (
            self.db.query(Course)
            .options(
                selectinload(Course.instructor),
                selectinload(Course.category),
                selectinload(Course.chapters).selectinload(Chapter.lessons),
            )
            .filter(Course.id == course_id)
            .first()
        )

    def get_published_paginated(
        self,
        page: int = 1,
        limit: int = 12,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Course], int]:
        query = self.db.query(Course).filter(Course.status == "PUBLISHED")
        if category_id:
            query = query.filter(Course.category_id == category_id)
        if search:
            query = query.filter(Course.title.ilike(f"%{search}%"))
        total = query.count()
        items = query.order_by(Course.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    def get_by_instructor_paginated(
        self, instructor_id: int, page: int = 1, limit: int = 12
    ) -> tuple[list[Course], int]:
        query = self.db.query(Course).filter(Course.instructor_id == instructor_id)
        total = query.count()
        items = query.order_by(Course.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    def get_pending(self) -> list[Course]:
        return self.db.query(Course).filter(Course.status == "PENDING").order_by(Course.created_at.asc()).all()

    def create(self, instructor_id: int, category_id: int, title: str, **kwargs) -> Course:
        course = Course(instructor_id=instructor_id, category_id=category_id, title=title, **kwargs)
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def update(self, course: Course, **kwargs) -> Course:
        for key, value in kwargs.items():
            if hasattr(course, key):
                setattr(course, key, value)
        self.db.commit()
        self.db.refresh(course)
        return course

    def count_lessons(self, course_id: int) -> int:
        return (
            self.db.query(Lesson)
            .join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(Chapter.course_id == course_id)
            .count()
        )


class ChapterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, chapter_id: int) -> Optional[Chapter]:
        return self.db.query(Chapter).filter(Chapter.id == chapter_id).first()

    def create(self, course_id: int, title: str, order_index: int = 1) -> Chapter:
        chapter = Chapter(course_id=course_id, title=title, order_index=order_index)
        self.db.add(chapter)
        self.db.commit()
        self.db.refresh(chapter)
        return chapter

    def update(self, chapter: Chapter, **kwargs) -> Chapter:
        for key, value in kwargs.items():
            if hasattr(chapter, key):
                setattr(chapter, key, value)
        self.db.commit()
        self.db.refresh(chapter)
        return chapter

    def delete(self, chapter: Chapter) -> None:
        self.db.delete(chapter)
        self.db.commit()


class LessonRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, lesson_id: int) -> Optional[Lesson]:
        return self.db.query(Lesson).filter(Lesson.id == lesson_id).first()

    def create(self, chapter_id: int, **kwargs) -> Lesson:
        lesson = Lesson(chapter_id=chapter_id, **kwargs)
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    def update(self, lesson: Lesson, **kwargs) -> Lesson:
        for key, value in kwargs.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    def delete(self, lesson: Lesson) -> None:
        self.db.delete(lesson)
        self.db.commit()
