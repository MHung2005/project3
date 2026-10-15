"""API Router – Enrollment & course progress (SDD §5.5)."""
from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DBSession, RequireStudent
from app.schemas.common import APIResponse
from app.schemas.progress import EnrollmentResponse
from app.services.progress_service import EnrollmentService

router = APIRouter()


@router.post("/courses/{course_id}/enroll", status_code=status.HTTP_201_CREATED, summary="[Student] Đăng ký khóa học")
def enroll_course(course_id: int, db: DBSession, current_user: RequireStudent):
    enrollment = EnrollmentService(db).enroll(user=current_user, course_id=course_id)
    return APIResponse(message="Đăng ký khóa học thành công!", data=EnrollmentResponse.model_validate(enrollment))


@router.get("/me/courses", summary="Khóa học của tôi & tiến độ (Dashboard học viên)")
def get_my_enrolled_courses(
    db: DBSession,
    current_user: CurrentUser,
    status_filter: Optional[str] = Query(default=None, alias="status", pattern="^(IN_PROGRESS|COMPLETED)$"),
):
    return APIResponse(data=EnrollmentService(db).get_my_courses(current_user.id, status_filter))


@router.get("/courses/{course_id}/progress", summary="Tổng quan tiến độ trong khóa học")
def get_course_progress(course_id: int, db: DBSession, current_user: CurrentUser):
    progress = EnrollmentService(db).get_course_progress(user_id=current_user.id, course_id=course_id)
    return APIResponse(data=progress)
