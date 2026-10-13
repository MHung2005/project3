"""API Router – Enrollment & Progress."""
from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession, RequireStudent
from app.schemas.progress import CompleteLessonRequest
from app.schemas.user import APIResponse
from app.services.progress_service import EnrollmentService

router = APIRouter()


@router.post("/courses/{course_id}/enroll", status_code=status.HTTP_201_CREATED, summary="[Student] Đăng ký khóa học")
def enroll_course(course_id: int, db: DBSession, current_user: RequireStudent):
    svc = EnrollmentService(db)
    enrollment = svc.enroll(user_id=current_user.id, course_id=course_id)
    return APIResponse(message="Đăng ký khóa học thành công!", data=enrollment)


@router.get("/courses/{course_id}/progress", summary="Tiến độ học tập trong khóa học")
def get_course_progress(course_id: int, db: DBSession, current_user: CurrentUser):
    svc = EnrollmentService(db)
    progress = svc.get_course_progress(user_id=current_user.id, course_id=course_id)
    return APIResponse(data=progress)


@router.post("/lessons/{lesson_id}/complete", summary="Đánh dấu hoàn thành bài học")
def complete_lesson(lesson_id: int, data: CompleteLessonRequest, db: DBSession, current_user: CurrentUser):
    svc = EnrollmentService(db)
    result = svc.complete_lesson(user_id=current_user.id, lesson_id=lesson_id, data=data)
    return APIResponse(message="Ghi nhận tiến độ thành công", data=result)
