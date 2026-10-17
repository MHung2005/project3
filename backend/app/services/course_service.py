"""Service – Course, Chapter, Lesson business logic (SDD §4.2)."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Chapter, Course, Enrollment, Lesson, User
from app.repositories.category_repository import CategoryRepository
from app.repositories.course_repository import ChapterRepository, CourseRepository, LessonRepository
from app.repositories.progress_repository import EnrollmentRepository, LessonProgressRepository
from app.repositories.user_repository import UserRepository
from app.schemas.course import (
    ChapterBriefResponse,
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    CourseCreate,
    CourseDetailResponse,
    CourseListResponse,
    CourseResponse,
    CourseUpdate,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    QuizBriefResponse,
    RejectCourseRequest,
    validate_lesson_content,
)
from app.schemas.progress import StudentProgressInfo
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.services.permissions import (
    can_manage_course,
    ensure_can_manage_course,
    ensure_course_editable,
    get_course_or_404,
    get_manageable_course,
)
from app.services.progress_service import ProgressCalculator
from app.services.storage_service import storage_service


def _lesson_response(lesson: Lesson, locked: bool = False) -> LessonResponse:
    data = LessonResponse.model_validate(lesson)
    if locked:
        return data.model_copy(update={"video_url": None, "document_url": None, "is_locked": True})
    return data


def _course_list(items: list[Course], total: int, page: int, limit: int) -> CourseListResponse:
    return CourseListResponse.build(
        items=[CourseResponse.model_validate(c) for c in items], total=total, page=page, limit=limit
    )


class CourseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    def _ensure_category(self, category_id: int) -> None:
        if not CategoryRepository(self.db).get_by_id(category_id):
            raise BadRequestError("Danh mục không tồn tại.")

    # ── Public ────────────────────────────────────────────────────────────────
    def get_published(self, page: int, limit: int, category_id: Optional[int], search: Optional[str]) -> CourseListResponse:
        items, total = self.repo.get_paginated(page, limit, status="PUBLISHED", category_id=category_id, search=search)
        return _course_list(items, total, page, limit)

    def get_detail(self, course_id: int, viewer: Optional[User] = None) -> CourseDetailResponse:
        """Course outline. Unpublished courses are visible to their owner and admins only;
        lesson content URLs are hidden unless the viewer is enrolled, manages the course,
        or the lesson is a free preview."""
        course = self.repo.get_detail(course_id)
        manages = course is not None and can_manage_course(viewer, course)
        if not course or (course.status != "PUBLISHED" and not manages):
            raise NotFoundError("Khóa học không tồn tại.")

        is_enrolled = bool(viewer) and self.enrollment_repo.get_by_user_and_course(viewer.id, course.id) is not None
        full_access = manages or is_enrolled

        chapters = []
        total_lessons = 0
        total_duration = 0
        for ch in course.chapters:
            lessons = [_lesson_response(ls, locked=not (full_access or ls.is_free_preview)) for ls in ch.lessons]
            total_lessons += len(lessons)
            total_duration += sum(ls.duration_seconds for ls in ch.lessons)
            chapters.append(ChapterResponse(**ChapterBriefResponse.model_validate(ch).model_dump(), lessons=lessons))

        return CourseDetailResponse(
            **CourseResponse.model_validate(course).model_dump(),
            chapters=chapters,
            quizzes=[QuizBriefResponse.model_validate(q) for q in course.quizzes],
            total_lessons=total_lessons,
            total_duration_seconds=total_duration,
            enrollment_count=self.repo.count_enrollments(course.id),
            is_enrolled=is_enrolled,
        )

    # ── Instructor ────────────────────────────────────────────────────────────
    def get_manageable_detail(self, course_id: int, user: User) -> CourseDetailResponse:
        """Course outline for its owner or an admin, including drafts."""
        get_manageable_course(self.db, course_id, user)
        return self.get_detail(course_id, user)

    def get_my_courses(self, instructor_id: int, page: int, limit: int, status_filter: Optional[str] = None) -> CourseListResponse:
        items, total = self.repo.get_paginated(page, limit, status=status_filter, instructor_id=instructor_id)
        return _course_list(items, total, page, limit)

    def create(self, instructor_id: int, data: CourseCreate) -> Course:
        self._ensure_category(data.category_id)
        return self.repo.create(
            instructor_id=instructor_id,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            thumbnail_url=data.thumbnail_url,
            status="DRAFT",
        )

    def update(self, course_id: int, user: User, data: CourseUpdate) -> Course:
        course = get_manageable_course(self.db, course_id, user)
        ensure_course_editable(course)
        update_data = data.model_dump(exclude_unset=True)
        # title and category_id are NOT NULL: an explicit null means "leave unchanged"
        for required in ("title", "category_id"):
            if required in update_data and update_data[required] is None:
                update_data.pop(required)
        if "category_id" in update_data:
            self._ensure_category(update_data["category_id"])
        return self.repo.update(course, **update_data)

    def delete(self, course_id: int, user: User) -> None:
        course = get_manageable_course(self.db, course_id, user)
        if course.status in ("PENDING", "PUBLISHED"):
            raise BadRequestError("Chỉ có thể xóa khóa học ở trạng thái Nháp hoặc Bị từ chối.")
        if self.repo.has_enrollments(course_id):
            raise BadRequestError("Không thể xóa khóa học đã có học viên.")
        self.repo.delete(course)

    def submit_for_review(self, course_id: int, user: User) -> Course:
        course = get_manageable_course(self.db, course_id, user)
        if course.status not in ("DRAFT", "REJECTED"):
            raise BadRequestError(f"Không thể gửi yêu cầu phê duyệt từ trạng thái '{course.status}'.")
        if self.repo.count_lessons(course_id) < 1:
            raise BadRequestError("Khóa học phải có ít nhất 1 bài học trước khi gửi phê duyệt.")
        return self.repo.update(course, status="PENDING")

    def enroll_student(self, course_id: int, user: User, student_email: str) -> Enrollment:
        """Instructor directly adds a student to the course by email."""
        course = get_manageable_course(self.db, course_id, user)
        if course.status != "PUBLISHED":
            raise BadRequestError("Chỉ có thể thêm học viên vào khóa học đã xuất bản.")
        student = UserRepository(self.db).get_by_email(student_email)
        if not student:
            raise NotFoundError(f"Không tìm thấy học viên với email: {student_email}")
        if not student.is_active:
            raise BadRequestError("Tài khoản học viên đang bị khóa.")
        if student.id == course.instructor_id:
            raise BadRequestError("Không thể thêm giảng viên phụ trách làm học viên.")
        if self.enrollment_repo.get_by_user_and_course(student.id, course_id):
            raise BadRequestError("Học viên đã đăng ký khóa học này.")
        return self.enrollment_repo.create(user_id=student.id, course_id=course_id)

    def get_students(self, course_id: int, user: User) -> list[StudentProgressInfo]:
        get_manageable_course(self.db, course_id, user)
        enrollments = self.enrollment_repo.get_by_course(course_id)
        total_lessons = self.repo.count_lessons(course_id)
        completed = LessonProgressRepository(self.db).count_completed_by_enrollments([e.id for e in enrollments])
        return [
            StudentProgressInfo(
                user_id=e.user.id,
                email=e.user.email,
                full_name=e.user.full_name,
                avatar_url=e.user.avatar_url,
                enrolled_at=e.enrolled_at,
                progress_percentage=e.progress_percentage,
                completed_lessons=completed.get(e.id, 0),
                total_lessons=total_lessons,
                status=e.status,
                completed_at=e.completed_at,
            )
            for e in enrollments
        ]

    # ── Admin ─────────────────────────────────────────────────────────────────
    def admin_list(
        self,
        page: int,
        limit: int,
        status_filter: Optional[str],
        category_id: Optional[int],
        search: Optional[str],
    ) -> CourseListResponse:
        items, total = self.repo.get_paginated(page, limit, status=status_filter, category_id=category_id, search=search)
        return _course_list(items, total, page, limit)

    def _get_pending(self, course_id: int) -> Course:
        course = get_course_or_404(self.db, course_id)
        if course.status != "PENDING":
            raise BadRequestError(f"Khóa học không ở trạng thái chờ duyệt (trạng thái hiện tại: {course.status}).")
        return course

    def approve_course(self, course_id: int) -> Course:
        course = self._get_pending(course_id)
        return self.repo.update(course, status="PUBLISHED", rejection_reason=None)

    def reject_course(self, course_id: int, data: RejectCourseRequest) -> Course:
        course = self._get_pending(course_id)
        return self.repo.update(course, status="REJECTED", rejection_reason=data.reason)


class ChapterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ChapterRepository(db)

    def list_for_course(self, course_id: int, user: User) -> list[Chapter]:
        get_manageable_course(self.db, course_id, user)
        return self.repo.get_by_course(course_id)

    def create(self, course_id: int, user: User, data: ChapterCreate) -> Chapter:
        course = get_manageable_course(self.db, course_id, user, "Bạn không có quyền thêm chương vào khóa học này.")
        ensure_course_editable(course)
        order = data.order_index or self.repo.next_order_index(course_id)
        return self.repo.create(course_id=course_id, title=data.title, order_index=order)

    def update(self, chapter_id: int, user: User, data: ChapterUpdate) -> Chapter:
        chapter = self._get_own_chapter(chapter_id, user)
        return self.repo.update(chapter, **data.model_dump(exclude_none=True))

    def delete(self, chapter_id: int, user: User) -> None:
        chapter = self._get_own_chapter(chapter_id, user)
        if self.repo.has_quizzes(chapter_id):
            raise BadRequestError("Chương học đang có bài kiểm tra. Vui lòng xóa hoặc chuyển bài kiểm tra trước.")
        course_id = chapter.course_id
        self.repo.delete(chapter)
        ProgressCalculator(self.db).recalculate_course(course_id)

    def _get_own_chapter(self, chapter_id: int, user: User) -> Chapter:
        chapter = self.repo.get_by_id(chapter_id)
        if not chapter:
            raise NotFoundError("Chương học không tồn tại.")
        ensure_can_manage_course(user, chapter.course, "Bạn không có quyền chỉnh sửa chương học này.")
        ensure_course_editable(chapter.course)
        return chapter


class LessonService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LessonRepository(db)

    def create(self, chapter_id: int, user: User, data: LessonCreate) -> Lesson:
        chapter = ChapterRepository(self.db).get_by_id(chapter_id)
        if not chapter:
            raise NotFoundError("Chương học không tồn tại.")
        ensure_can_manage_course(user, chapter.course, "Bạn không có quyền thêm bài học vào chương này.")
        ensure_course_editable(chapter.course)
        lesson_data = data.model_dump()
        lesson_data["order_index"] = data.order_index or self.repo.next_order_index(chapter_id)
        lesson = self.repo.create(chapter_id=chapter_id, **lesson_data)
        ProgressCalculator(self.db).recalculate_course(chapter.course_id)
        return lesson

    def update(self, lesson_id: int, user: User, data: LessonUpdate) -> Lesson:
        lesson = self._get_own_lesson(lesson_id, user)
        update_data = data.model_dump(exclude_unset=True)
        # NOT NULL columns: an explicit null means "leave unchanged"
        for required in ("title", "lesson_type", "duration_seconds", "order_index", "is_free_preview"):
            if required in update_data and update_data[required] is None:
                update_data.pop(required)
        # Validate the lesson as it will look after the update
        try:
            validate_lesson_content(
                update_data.get("lesson_type", lesson.lesson_type),
                update_data.get("video_url", lesson.video_url),
                update_data.get("document_url", lesson.document_url),
            )
        except ValueError as exc:
            raise BadRequestError(str(exc))
        return self.repo.update(lesson, **update_data)

    def delete(self, lesson_id: int, user: User) -> None:
        lesson = self._get_own_lesson(lesson_id, user)
        course_id = lesson.chapter.course_id
        self.repo.delete(lesson)
        ProgressCalculator(self.db).recalculate_course(course_id)

    def get_for_learning(self, lesson_id: int, user: User) -> LessonResponse:
        """Full lesson content (document URL presigned) for enrolled learners or course managers."""
        lesson = self.repo.get_with_course(lesson_id)
        if not lesson:
            raise NotFoundError("Bài học không tồn tại.")
        course = lesson.chapter.course
        if not can_manage_course(user, course):
            if course.status != "PUBLISHED":
                raise NotFoundError("Bài học không tồn tại.")
            enrolled = EnrollmentRepository(self.db).get_by_user_and_course(user.id, course.id) is not None
            if not (enrolled or lesson.is_free_preview):
                raise ForbiddenError("Bạn cần đăng ký khóa học để xem bài học này.")
        data = _lesson_response(lesson)
        if data.document_url:
            data = data.model_copy(update={"document_url": storage_service.resolve_download_url(data.document_url)})
        return data

    def _get_own_lesson(self, lesson_id: int, user: User) -> Lesson:
        lesson = self.repo.get_with_course(lesson_id)
        if not lesson:
            raise NotFoundError("Bài học không tồn tại.")
        course = lesson.chapter.course
        ensure_can_manage_course(user, course, "Bạn không có quyền chỉnh sửa bài học này.")
        ensure_course_editable(course)
        return lesson
