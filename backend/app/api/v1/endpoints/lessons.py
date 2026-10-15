"""API Router – Lessons: authoring, learning view and per-lesson progress (SDD §4.3, §5.4, §5.5)."""
from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession, RequireInstructor
from app.schemas.common import APIResponse
from app.schemas.course import LessonCreate, LessonResponse, LessonUpdate
from app.schemas.progress import CompleteLessonRequest, SaveLessonPositionRequest
from app.services.course_service import LessonService
from app.services.progress_service import EnrollmentService

router = APIRouter()


# ── Instructor: Lesson Management ─────────────────────────────────────────────
@router.post(
    "/instructor/chapters/{chapter_id}/lessons",
    status_code=status.HTTP_201_CREATED,
    summary="[Instructor] Thêm bài học (Video YouTube hoặc Tài liệu)",
)
def create_lesson(chapter_id: int, data: LessonCreate, db: DBSession, current_user: RequireInstructor):
    lesson = LessonService(db).create(chapter_id=chapter_id, user=current_user, data=data)
    return APIResponse(message="Thêm bài học thành công", data=LessonResponse.model_validate(lesson))


@router.put("/instructor/lessons/{lesson_id}", summary="[Instructor] Cập nhật bài học")
def update_lesson(lesson_id: int, data: LessonUpdate, db: DBSession, current_user: RequireInstructor):
    lesson = LessonService(db).update(lesson_id=lesson_id, user=current_user, data=data)
    return APIResponse(message="Cập nhật bài học thành công", data=LessonResponse.model_validate(lesson))


@router.delete("/instructor/lessons/{lesson_id}", summary="[Instructor] Xóa bài học")
def delete_lesson(lesson_id: int, db: DBSession, current_user: RequireInstructor):
    LessonService(db).delete(lesson_id=lesson_id, user=current_user)
    return APIResponse(message="Xóa bài học thành công")


# ── Learner ───────────────────────────────────────────────────────────────────
@router.get("/lessons/{lesson_id}", summary="Nội dung bài học (học viên đã đăng ký / học thử)")
def get_lesson(lesson_id: int, db: DBSession, current_user: CurrentUser):
    return APIResponse(data=LessonService(db).get_for_learning(lesson_id, current_user))


@router.get("/lessons/{lesson_id}/progress", summary="Vị trí đã xem lần trước của bài học")
def get_lesson_progress(lesson_id: int, db: DBSession, current_user: CurrentUser):
    return APIResponse(data=EnrollmentService(db).get_lesson_progress(current_user.id, lesson_id))


@router.put("/lessons/{lesson_id}/progress", summary="Lưu vị trí đang xem (gọi định kỳ từ Player)")
def save_lesson_progress(lesson_id: int, data: SaveLessonPositionRequest, db: DBSession, current_user: CurrentUser):
    result = EnrollmentService(db).save_position(current_user.id, lesson_id, data)
    return APIResponse(message="Đã lưu vị trí xem", data=result)


@router.post("/lessons/{lesson_id}/complete", summary="Đánh dấu hoàn thành bài học (video >= 80% / đọc tài liệu)")
def complete_lesson(lesson_id: int, data: CompleteLessonRequest, db: DBSession, current_user: CurrentUser):
    result = EnrollmentService(db).complete_lesson(user_id=current_user.id, lesson_id=lesson_id, data=data)
    return APIResponse(message="Ghi nhận tiến độ thành công", data=result)
