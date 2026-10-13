"""Service – Course, Chapter, Lesson business logic."""
import math
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Chapter, Course, Lesson, User
from app.repositories.course_repository import ChapterRepository, CourseRepository, LessonRepository
from app.repositories.progress_repository import EnrollmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.course import (
    ChapterCreate,
    ChapterUpdate,
    CourseCreate,
    CourseListResponse,
    CourseUpdate,
    LessonCreate,
    LessonUpdate,
    RejectCourseRequest,
)


class CourseService:
    def __init__(self, db: Session):
        self.repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    # ── Public ────────────────────────────────────────────────────────────────
    def get_published(self, page: int, limit: int, category_id: Optional[int], search: Optional[str]) -> CourseListResponse:
        items, total = self.repo.get_published_paginated(page, limit, category_id, search)
        pages = math.ceil(total / limit) if total > 0 else 1
        return CourseListResponse(items=items, total=total, page=page, limit=limit, pages=pages)

    def get_detail(self, course_id: int) -> Course:
        course = self.repo.get_detail(course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khóa học không tồn tại.")
        return course

    # ── Instructor ────────────────────────────────────────────────────────────
    def get_my_courses(self, instructor_id: int, page: int, limit: int) -> CourseListResponse:
        items, total = self.repo.get_by_instructor_paginated(instructor_id, page, limit)
        pages = math.ceil(total / limit) if total > 0 else 1
        return CourseListResponse(items=items, total=total, page=page, limit=limit, pages=pages)

    def create(self, instructor_id: int, data: CourseCreate) -> Course:
        return self.repo.create(
            instructor_id=instructor_id,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            thumbnail_url=data.thumbnail_url,
            status="DRAFT",
        )

    def update(self, course_id: int, instructor_id: int, data: CourseUpdate) -> Course:
        course = self._get_own_course(course_id, instructor_id)
        update_data = data.model_dump(exclude_none=True)
        return self.repo.update(course, **update_data)

    def submit_for_review(self, course_id: int, instructor_id: int) -> Course:
        course = self._get_own_course(course_id, instructor_id)
        if course.status not in ("DRAFT", "REJECTED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể gửi yêu cầu phê duyệt từ trạng thái '{course.status}'.",
            )
        if self.repo.count_lessons(course_id) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khóa học phải có ít nhất 1 bài học trước khi gửi phê duyệt.",
            )
        return self.repo.update(course, status="PENDING")

    def enroll_student(self, course_id: int, instructor_id: int, student_email: str) -> None:
        """Instructor directly adds a student to the course by email."""
        course = self._get_own_course(course_id, instructor_id)
        user_repo = UserRepository(self.repo.db)
        student = user_repo.get_by_email(student_email)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy học viên với email: {student_email}")
        existing = self.enrollment_repo.get_by_user_and_course(student.id, course_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Học viên đã đăng ký khóa học này.")
        self.enrollment_repo.create(user_id=student.id, course_id=course_id)

    def get_students(self, course_id: int, instructor_id: int):
        self._get_own_course(course_id, instructor_id)
        enrollments = self.enrollment_repo.get_by_course(course_id)
        user_repo = UserRepository(self.repo.db)
        result = []
        for e in enrollments:
            user = user_repo.get_by_id(e.user_id)
            if user:
                result.append({
                    "user_id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "enrolled_at": e.enrolled_at,
                    "progress_percentage": e.progress_percentage,
                    "status": e.status,
                    "completed_at": e.completed_at,
                })
        return result

    # ── Admin ─────────────────────────────────────────────────────────────────
    def get_pending_courses(self) -> list[Course]:
        return self.repo.get_pending()

    def approve_course(self, course_id: int) -> Course:
        course = self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khóa học không tồn tại.")
        if course.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Khóa học không ở trạng thái chờ duyệt (trạng thái hiện tại: {course.status}).",
            )
        return self.repo.update(course, status="PUBLISHED", rejection_reason=None)

    def reject_course(self, course_id: int, data: RejectCourseRequest) -> Course:
        course = self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khóa học không tồn tại.")
        if course.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Khóa học không ở trạng thái chờ duyệt (trạng thái hiện tại: {course.status}).",
            )
        return self.repo.update(course, status="REJECTED", rejection_reason=data.reason)

    # ── Internal helper ───────────────────────────────────────────────────────
    def _get_own_course(self, course_id: int, instructor_id: int) -> Course:
        course = self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khóa học không tồn tại.")
        if course.instructor_id != instructor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền chỉnh sửa khóa học này.",
            )
        return course


class ChapterService:
    def __init__(self, db: Session):
        self.chapter_repo = ChapterRepository(db)
        self.course_repo = CourseRepository(db)

    def create(self, course_id: int, instructor_id: int, data: ChapterCreate) -> Chapter:
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khóa học không tồn tại.")
        if course.instructor_id != instructor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thêm chương vào khóa học này.")
        return self.chapter_repo.create(course_id=course_id, title=data.title, order_index=data.order_index)

    def update(self, chapter_id: int, instructor_id: int, data: ChapterUpdate) -> Chapter:
        chapter = self._get_own_chapter(chapter_id, instructor_id)
        update_data = data.model_dump(exclude_none=True)
        return self.chapter_repo.update(chapter, **update_data)

    def delete(self, chapter_id: int, instructor_id: int) -> None:
        chapter = self._get_own_chapter(chapter_id, instructor_id)
        self.chapter_repo.delete(chapter)

    def _get_own_chapter(self, chapter_id: int, instructor_id: int) -> Chapter:
        chapter = self.chapter_repo.get_by_id(chapter_id)
        if not chapter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chương học không tồn tại.")
        course = self.course_repo.get_by_id(chapter.course_id)
        if course.instructor_id != instructor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền chỉnh sửa chương học này.")
        return chapter


class LessonService:
    def __init__(self, db: Session):
        self.lesson_repo = LessonRepository(db)
        self.chapter_repo = ChapterRepository(db)
        self.course_repo = CourseRepository(db)

    def create(self, chapter_id: int, instructor_id: int, data: LessonCreate) -> Lesson:
        chapter = self.chapter_repo.get_by_id(chapter_id)
        if not chapter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chương học không tồn tại.")
        course = self.course_repo.get_by_id(chapter.course_id)
        if course.instructor_id != instructor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thêm bài học vào chương này.")
        lesson_data = data.model_dump()
        lesson_data["chapter_id"] = chapter_id
        chapter_id_val = lesson_data.pop("chapter_id")
        return self.lesson_repo.create(chapter_id=chapter_id, **data.model_dump())

    def update(self, lesson_id: int, instructor_id: int, data: LessonUpdate) -> Lesson:
        lesson = self._get_own_lesson(lesson_id, instructor_id)
        update_data = data.model_dump(exclude_none=True)
        return self.lesson_repo.update(lesson, **update_data)

    def delete(self, lesson_id: int, instructor_id: int) -> None:
        lesson = self._get_own_lesson(lesson_id, instructor_id)
        self.lesson_repo.delete(lesson)

    def _get_own_lesson(self, lesson_id: int, instructor_id: int) -> Lesson:
        lesson = self.lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bài học không tồn tại.")
        chapter = self.chapter_repo.get_by_id(lesson.chapter_id)
        course = self.course_repo.get_by_id(chapter.course_id)
        if course.instructor_id != instructor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền chỉnh sửa bài học này.")
        return lesson
