"""Shared access checks for the service layer."""
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models import Course, User
from app.repositories.course_repository import CourseRepository


def is_admin(user: User | None) -> bool:
    return user is not None and user.role == "ADMIN"


def can_manage_course(user: User | None, course: Course) -> bool:
    """Owner instructor or any admin may manage a course."""
    return user is not None and (is_admin(user) or course.instructor_id == user.id)


def ensure_can_manage_course(user: User, course: Course, detail: str = "Bạn không có quyền chỉnh sửa khóa học này.") -> None:
    if not can_manage_course(user, course):
        raise ForbiddenError(detail)


def ensure_course_editable(course: Course) -> None:
    """Content is frozen while an admin is reviewing the course."""
    if course.status == "PENDING":
        raise BadRequestError("Khóa học đang chờ phê duyệt, không thể chỉnh sửa nội dung.")


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = CourseRepository(db).get_by_id(course_id)
    if not course:
        raise NotFoundError("Khóa học không tồn tại.")
    return course


def get_manageable_course(
    db: Session, course_id: int, user: User, detail: str = "Bạn không có quyền chỉnh sửa khóa học này."
) -> Course:
    course = get_course_or_404(db, course_id)
    ensure_can_manage_course(user, course, detail)
    return course
