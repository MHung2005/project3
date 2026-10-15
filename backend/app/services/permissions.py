"""Shared access checks and HTTP error helpers for the service layer."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Course, User
from app.repositories.course_repository import CourseRepository


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def is_admin(user: User | None) -> bool:
    return user is not None and user.role == "ADMIN"


def can_manage_course(user: User | None, course: Course) -> bool:
    """Owner instructor or any admin may manage a course."""
    return user is not None and (is_admin(user) or course.instructor_id == user.id)


def ensure_can_manage_course(user: User, course: Course, detail: str = "Bạn không có quyền chỉnh sửa khóa học này.") -> None:
    if not can_manage_course(user, course):
        raise forbidden(detail)


def ensure_course_editable(course: Course) -> None:
    """Content is frozen while an admin is reviewing the course."""
    if course.status == "PENDING":
        raise bad_request("Khóa học đang chờ phê duyệt, không thể chỉnh sửa nội dung.")


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = CourseRepository(db).get_by_id(course_id)
    if not course:
        raise not_found("Khóa học không tồn tại.")
    return course


def get_manageable_course(
    db: Session, course_id: int, user: User, detail: str = "Bạn không có quyền chỉnh sửa khóa học này."
) -> Course:
    course = get_course_or_404(db, course_id)
    ensure_can_manage_course(user, course, detail)
    return course
