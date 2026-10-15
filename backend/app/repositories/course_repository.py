"""Repository – Course, Chapter, Lesson data access."""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.models import Chapter, Course, Enrollment, Lesson, Quiz


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Course ────────────────────────────────────────────────────────────────
    def get_by_id(self, course_id: int) -> Optional[Course]:
        return self.db.get(Course, course_id)

    def get_detail(self, course_id: int) -> Optional[Course]:
        return (
            self.db.query(Course)
            .options(
                selectinload(Course.instructor),
                selectinload(Course.category),
                selectinload(Course.chapters).selectinload(Chapter.lessons),
                selectinload(Course.quizzes),
            )
            .filter(Course.id == course_id)
            .first()
        )

    def get_paginated(
        self,
        page: int = 1,
        limit: int = 12,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        instructor_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Course], int]:
        query = self.db.query(Course)
        if status:
            query = query.filter(Course.status == status)
        if category_id:
            query = query.filter(Course.category_id == category_id)
        if instructor_id:
            query = query.filter(Course.instructor_id == instructor_id)
        if search:
            query = query.filter(Course.title.ilike(f"%{search}%"))
        total = query.count()
        # Pending courses are reviewed oldest-first, everything else newest-first
        order = Course.updated_at.asc() if status == "PENDING" else Course.created_at.desc()
        items = (
            query.options(selectinload(Course.instructor), selectinload(Course.category))
            .order_by(order, Course.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return items, total

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

    def delete(self, course: Course) -> None:
        self.db.delete(course)
        self.db.commit()

    def count_lessons(self, course_id: int) -> int:
        return (
            self.db.query(Lesson)
            .join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(Chapter.course_id == course_id)
            .count()
        )

    def get_lesson_ids(self, course_id: int) -> list[int]:
        rows = (
            self.db.query(Lesson.id)
            .join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(Chapter.course_id == course_id)
            .order_by(Chapter.order_index, Lesson.order_index, Lesson.id)
            .all()
        )
        return [r[0] for r in rows]

    def count_enrollments(self, course_id: int) -> int:
        return self.db.query(func.count(Enrollment.id)).filter(Enrollment.course_id == course_id).scalar() or 0

    def has_enrollments(self, course_id: int) -> bool:
        return self.db.query(Enrollment.id).filter(Enrollment.course_id == course_id).first() is not None


class ChapterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, chapter_id: int) -> Optional[Chapter]:
        return self.db.get(Chapter, chapter_id)

    def get_by_course(self, course_id: int) -> list[Chapter]:
        return (
            self.db.query(Chapter)
            .options(selectinload(Chapter.lessons))
            .filter(Chapter.course_id == course_id)
            .order_by(Chapter.order_index, Chapter.id)
            .all()
        )

    def next_order_index(self, course_id: int) -> int:
        current = self.db.query(func.max(Chapter.order_index)).filter(Chapter.course_id == course_id).scalar()
        return (current or 0) + 1

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

    def has_quizzes(self, chapter_id: int) -> bool:
        return self.db.query(Quiz.id).filter(Quiz.chapter_id == chapter_id).first() is not None


class LessonRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_with_course(self, lesson_id: int) -> Optional[Lesson]:
        """Load a lesson together with its chapter and course (for permission checks)."""
        return (
            self.db.query(Lesson)
            .options(selectinload(Lesson.chapter).selectinload(Chapter.course))
            .filter(Lesson.id == lesson_id)
            .first()
        )

    def next_order_index(self, chapter_id: int) -> int:
        current = self.db.query(func.max(Lesson.order_index)).filter(Lesson.chapter_id == chapter_id).scalar()
        return (current or 0) + 1

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
