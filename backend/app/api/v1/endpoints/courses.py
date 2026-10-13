"""API Router – Courses, Chapters, Lessons."""
from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DBSession, RequireAdmin, RequireInstructor
from app.schemas.course import (
    ChapterCreate,
    ChapterUpdate,
    CourseCreate,
    CourseDetailResponse,
    CourseUpdate,
    EnrollStudentRequest,
    LessonCreate,
    LessonUpdate,
    RejectCourseRequest,
)
from app.schemas.user import APIResponse
from app.services.course_service import ChapterService, CourseService, LessonService

router = APIRouter()


# ── Public Course Endpoints ───────────────────────────────────────────────────
@router.get("/courses", summary="Danh sách khóa học đã xuất bản (Public)")
def get_published_courses(
    db: DBSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=50),
    category_id: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None),
):
    svc = CourseService(db)
    result = svc.get_published(page=page, limit=limit, category_id=category_id, search=search)
    return APIResponse(data=result)


@router.get("/courses/{course_id}", summary="Chi tiết khóa học (Public)")
def get_course_detail(course_id: int, db: DBSession):
    svc = CourseService(db)
    course = svc.get_detail(course_id)
    return APIResponse(data=CourseDetailResponse.model_validate(course))


# ── Instructor: Course Management ─────────────────────────────────────────────
@router.get("/instructor/courses", summary="[Instructor] Danh sách khóa học của tôi")
def get_my_courses(
    db: DBSession,
    current_user: RequireInstructor,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=50),
):
    svc = CourseService(db)
    result = svc.get_my_courses(current_user.id, page=page, limit=limit)
    return APIResponse(data=result)


@router.post("/instructor/courses", status_code=status.HTTP_201_CREATED, summary="[Instructor] Tạo khóa học mới")
def create_course(data: CourseCreate, db: DBSession, current_user: RequireInstructor):
    svc = CourseService(db)
    course = svc.create(instructor_id=current_user.id, data=data)
    return APIResponse(message="Tạo khóa học thành công", data=course)


@router.put("/instructor/courses/{course_id}", summary="[Instructor] Cập nhật khóa học")
def update_course(course_id: int, data: CourseUpdate, db: DBSession, current_user: RequireInstructor):
    svc = CourseService(db)
    course = svc.update(course_id=course_id, instructor_id=current_user.id, data=data)
    return APIResponse(message="Cập nhật khóa học thành công", data=course)


@router.post("/instructor/courses/{course_id}/submit-review", summary="[Instructor] Gửi yêu cầu phê duyệt")
def submit_for_review(course_id: int, db: DBSession, current_user: RequireInstructor):
    svc = CourseService(db)
    course = svc.submit_for_review(course_id=course_id, instructor_id=current_user.id)
    return APIResponse(message="Đã gửi yêu cầu phê duyệt thành công. Vui lòng chờ Admin xem xét.", data=course)


@router.post("/instructor/courses/{course_id}/enroll-student", summary="[Instructor] Thêm học viên vào khóa học")
def enroll_student(course_id: int, data: EnrollStudentRequest, db: DBSession, current_user: RequireInstructor):
    svc = CourseService(db)
    svc.enroll_student(course_id=course_id, instructor_id=current_user.id, student_email=data.student_email)
    return APIResponse(message=f"Đã thêm học viên {data.student_email} vào khóa học.")


@router.get("/instructor/courses/{course_id}/students", summary="[Instructor] Danh sách học viên và tiến độ")
def get_students_progress(course_id: int, db: DBSession, current_user: RequireInstructor):
    svc = CourseService(db)
    students = svc.get_students(course_id=course_id, instructor_id=current_user.id)
    return APIResponse(data=students)


# ── Instructor: Chapter Management ────────────────────────────────────────────
@router.post("/instructor/courses/{course_id}/chapters", status_code=status.HTTP_201_CREATED, summary="[Instructor] Thêm chương học")
def create_chapter(course_id: int, data: ChapterCreate, db: DBSession, current_user: RequireInstructor):
    svc = ChapterService(db)
    chapter = svc.create(course_id=course_id, instructor_id=current_user.id, data=data)
    return APIResponse(message="Thêm chương học thành công", data=chapter)


@router.put("/instructor/chapters/{chapter_id}", summary="[Instructor] Cập nhật chương học")
def update_chapter(chapter_id: int, data: ChapterUpdate, db: DBSession, current_user: RequireInstructor):
    svc = ChapterService(db)
    chapter = svc.update(chapter_id=chapter_id, instructor_id=current_user.id, data=data)
    return APIResponse(message="Cập nhật chương học thành công", data=chapter)


@router.delete("/instructor/chapters/{chapter_id}", summary="[Instructor] Xóa chương học")
def delete_chapter(chapter_id: int, db: DBSession, current_user: RequireInstructor):
    svc = ChapterService(db)
    svc.delete(chapter_id=chapter_id, instructor_id=current_user.id)
    return APIResponse(message="Xóa chương học thành công")


# ── Instructor: Lesson Management ─────────────────────────────────────────────
@router.post("/instructor/chapters/{chapter_id}/lessons", status_code=status.HTTP_201_CREATED, summary="[Instructor] Thêm bài học")
def create_lesson(chapter_id: int, data: LessonCreate, db: DBSession, current_user: RequireInstructor):
    svc = LessonService(db)
    lesson = svc.create(chapter_id=chapter_id, instructor_id=current_user.id, data=data)
    return APIResponse(message="Thêm bài học thành công", data=lesson)


@router.put("/instructor/lessons/{lesson_id}", summary="[Instructor] Cập nhật bài học")
def update_lesson(lesson_id: int, data: LessonUpdate, db: DBSession, current_user: RequireInstructor):
    svc = LessonService(db)
    lesson = svc.update(lesson_id=lesson_id, instructor_id=current_user.id, data=data)
    return APIResponse(message="Cập nhật bài học thành công", data=lesson)


@router.delete("/instructor/lessons/{lesson_id}", summary="[Instructor] Xóa bài học")
def delete_lesson(lesson_id: int, db: DBSession, current_user: RequireInstructor):
    svc = LessonService(db)
    svc.delete(lesson_id=lesson_id, instructor_id=current_user.id)
    return APIResponse(message="Xóa bài học thành công")


# ── Admin: Course Moderation ───────────────────────────────────────────────────
@router.get("/admin/courses", summary="[Admin] Danh sách khóa học theo trạng thái")
def admin_get_courses(
    db: DBSession,
    current_user: RequireAdmin,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    svc = CourseService(db)
    if status_filter == "PENDING":
        courses = svc.get_pending_courses()
        return APIResponse(data={"items": courses, "total": len(courses)})
    # General paginated list for admin
    result = svc.get_published(page=page, limit=limit, category_id=None, search=None)
    return APIResponse(data=result)


@router.post("/admin/courses/{course_id}/approve", summary="[Admin] Phê duyệt khóa học")
def approve_course(course_id: int, db: DBSession, current_user: RequireAdmin):
    svc = CourseService(db)
    course = svc.approve_course(course_id)
    return APIResponse(message="Khóa học đã được phê duyệt và xuất bản thành công.", data=course)


@router.post("/admin/courses/{course_id}/reject", summary="[Admin] Từ chối khóa học")
def reject_course(course_id: int, data: RejectCourseRequest, db: DBSession, current_user: RequireAdmin):
    svc = CourseService(db)
    course = svc.reject_course(course_id, data)
    return APIResponse(message="Đã từ chối khóa học và gửi lý do cho giảng viên.", data=course)
