"""API Router – Courses & Chapters, course moderation (SDD §5.4)."""
from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.deps import DBSession, OptionalUser, RequireAdmin, RequireInstructor
from app.schemas.common import APIResponse
from app.schemas.course import (
    ChapterBriefResponse,
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    EnrollStudentRequest,
    RejectCourseRequest,
)
from app.schemas.progress import EnrollmentResponse
from app.services.course_service import ChapterService, CourseService

router = APIRouter()

COURSE_STATUS_PATTERN = "^(DRAFT|PENDING|PUBLISHED|REJECTED)$"


# ── Public Course Endpoints ───────────────────────────────────────────────────
@router.get("/courses", summary="Danh sách khóa học đã xuất bản (Public)")
def get_published_courses(
    db: DBSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=50),
    category_id: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
):
    result = CourseService(db).get_published(page=page, limit=limit, category_id=category_id, search=search)
    return APIResponse(data=result)


@router.get("/courses/{course_id}", summary="Chi tiết khóa học, đề cương và giảng viên (Public)")
def get_course_detail(course_id: int, db: DBSession, viewer: OptionalUser):
    return APIResponse(data=CourseService(db).get_detail(course_id, viewer))


# ── Instructor: Course Management ─────────────────────────────────────────────
@router.get("/instructor/courses", summary="[Instructor] Danh sách khóa học của tôi")
def get_my_courses(
    db: DBSession,
    current_user: RequireInstructor,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=50),
    status_filter: Optional[str] = Query(default=None, alias="status", pattern=COURSE_STATUS_PATTERN),
):
    result = CourseService(db).get_my_courses(current_user.id, page=page, limit=limit, status_filter=status_filter)
    return APIResponse(data=result)


@router.post("/instructor/courses", status_code=status.HTTP_201_CREATED, summary="[Instructor] Tạo khóa học mới (DRAFT)")
def create_course(data: CourseCreate, db: DBSession, current_user: RequireInstructor):
    course = CourseService(db).create(instructor_id=current_user.id, data=data)
    return APIResponse(message="Tạo khóa học thành công", data=CourseResponse.model_validate(course))


@router.get("/instructor/courses/{course_id}", summary="[Instructor] Chi tiết khóa học của tôi (kể cả bản nháp)")
def get_my_course_detail(course_id: int, db: DBSession, current_user: RequireInstructor):
    return APIResponse(data=CourseService(db).get_manageable_detail(course_id, current_user))


@router.put("/instructor/courses/{course_id}", summary="[Instructor] Cập nhật khóa học")
def update_course(course_id: int, data: CourseUpdate, db: DBSession, current_user: RequireInstructor):
    course = CourseService(db).update(course_id=course_id, user=current_user, data=data)
    return APIResponse(message="Cập nhật khóa học thành công", data=CourseResponse.model_validate(course))


@router.delete("/instructor/courses/{course_id}", summary="[Instructor] Xóa khóa học (chỉ DRAFT/REJECTED, chưa có học viên)")
def delete_course(course_id: int, db: DBSession, current_user: RequireInstructor):
    CourseService(db).delete(course_id=course_id, user=current_user)
    return APIResponse(message="Xóa khóa học thành công")


@router.post("/instructor/courses/{course_id}/submit-review", summary="[Instructor] Gửi yêu cầu phê duyệt")
def submit_for_review(course_id: int, db: DBSession, current_user: RequireInstructor):
    course = CourseService(db).submit_for_review(course_id=course_id, user=current_user)
    return APIResponse(
        message="Đã gửi yêu cầu phê duyệt thành công. Vui lòng chờ Admin xem xét.",
        data=CourseResponse.model_validate(course),
    )


@router.post(
    "/instructor/courses/{course_id}/enroll-student",
    status_code=status.HTTP_201_CREATED,
    summary="[Instructor] Thêm học viên vào khóa học bằng email",
)
def enroll_student(course_id: int, data: EnrollStudentRequest, db: DBSession, current_user: RequireInstructor):
    enrollment = CourseService(db).enroll_student(
        course_id=course_id, user=current_user, student_email=data.student_email
    )
    return APIResponse(
        message=f"Đã thêm học viên {data.student_email} vào khóa học.",
        data=EnrollmentResponse.model_validate(enrollment),
    )


@router.get("/instructor/courses/{course_id}/students", summary="[Instructor] Danh sách học viên và tiến độ")
def get_students_progress(course_id: int, db: DBSession, current_user: RequireInstructor):
    students = CourseService(db).get_students(course_id=course_id, user=current_user)
    return APIResponse(data=students)


# ── Instructor: Chapter Management ────────────────────────────────────────────
@router.get("/instructor/courses/{course_id}/chapters", summary="[Instructor] Danh sách chương (kèm bài học)")
def list_chapters(course_id: int, db: DBSession, current_user: RequireInstructor):
    chapters = ChapterService(db).list_for_course(course_id, current_user)
    return APIResponse(data=[ChapterResponse.model_validate(c) for c in chapters])


@router.post(
    "/instructor/courses/{course_id}/chapters",
    status_code=status.HTTP_201_CREATED,
    summary="[Instructor] Thêm chương học",
)
def create_chapter(course_id: int, data: ChapterCreate, db: DBSession, current_user: RequireInstructor):
    chapter = ChapterService(db).create(course_id=course_id, user=current_user, data=data)
    return APIResponse(message="Thêm chương học thành công", data=ChapterBriefResponse.model_validate(chapter))


@router.put("/instructor/chapters/{chapter_id}", summary="[Instructor] Cập nhật chương học")
def update_chapter(chapter_id: int, data: ChapterUpdate, db: DBSession, current_user: RequireInstructor):
    chapter = ChapterService(db).update(chapter_id=chapter_id, user=current_user, data=data)
    return APIResponse(message="Cập nhật chương học thành công", data=ChapterBriefResponse.model_validate(chapter))


@router.delete("/instructor/chapters/{chapter_id}", summary="[Instructor] Xóa chương học")
def delete_chapter(chapter_id: int, db: DBSession, current_user: RequireInstructor):
    ChapterService(db).delete(chapter_id=chapter_id, user=current_user)
    return APIResponse(message="Xóa chương học thành công")


# ── Admin: Course Moderation ──────────────────────────────────────────────────
@router.get("/admin/courses", summary="[Admin] Danh sách khóa học theo trạng thái (vd. ?status=PENDING)")
def admin_get_courses(
    db: DBSession,
    current_user: RequireAdmin,
    status_filter: Optional[str] = Query(default=None, alias="status", pattern=COURSE_STATUS_PATTERN),
    category_id: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    result = CourseService(db).admin_list(page, limit, status_filter, category_id, search)
    return APIResponse(data=result)


@router.get("/admin/courses/{course_id}", summary="[Admin] Xem toàn bộ nội dung khóa học để kiểm duyệt")
def admin_get_course(course_id: int, db: DBSession, current_user: RequireAdmin):
    return APIResponse(data=CourseService(db).get_detail(course_id, current_user))


@router.post("/admin/courses/{course_id}/approve", summary="[Admin] Phê duyệt khóa học")
def approve_course(course_id: int, db: DBSession, current_user: RequireAdmin):
    course = CourseService(db).approve_course(course_id)
    return APIResponse(
        message="Khóa học đã được phê duyệt và xuất bản thành công.",
        data=CourseResponse.model_validate(course),
    )


@router.post("/admin/courses/{course_id}/reject", summary="[Admin] Từ chối khóa học kèm lý do")
def reject_course(course_id: int, data: RejectCourseRequest, db: DBSession, current_user: RequireAdmin):
    course = CourseService(db).reject_course(course_id, data)
    return APIResponse(
        message="Đã từ chối khóa học và gửi lý do cho giảng viên.",
        data=CourseResponse.model_validate(course),
    )
