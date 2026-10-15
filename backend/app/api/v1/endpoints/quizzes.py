"""API Router – Question bank & Quizzes (SDD §4.4, §5.6)."""
from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DBSession, RequireInstructor
from app.schemas.common import APIResponse
from app.schemas.quiz import (
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
    QuizCreate,
    QuizResponse,
    QuizSubmitRequest,
    QuizUpdate,
)
from app.services.quiz_service import QuestionService, QuizService

router = APIRouter()


# ── Instructor: Question Bank ─────────────────────────────────────────────────
@router.get("/instructor/questions", summary="[Instructor] Ngân hàng câu hỏi của tôi")
def get_my_questions(
    db: DBSession,
    current_user: RequireInstructor,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None, max_length=100),
):
    return APIResponse(data=QuestionService(db).get_my_questions(current_user, page, limit, search))


@router.get("/instructor/questions/{question_id}", summary="[Instructor] Chi tiết câu hỏi")
def get_question(question_id: int, db: DBSession, current_user: RequireInstructor):
    question = QuestionService(db).get_own(question_id, current_user)
    return APIResponse(data=QuestionResponse.model_validate(question))


@router.post("/instructor/questions", status_code=status.HTTP_201_CREATED, summary="[Instructor] Tạo câu hỏi mới")
def create_question(data: QuestionCreate, db: DBSession, current_user: RequireInstructor):
    question = QuestionService(db).create(instructor_id=current_user.id, data=data)
    return APIResponse(message="Tạo câu hỏi thành công", data=QuestionResponse.model_validate(question))


@router.put("/instructor/questions/{question_id}", summary="[Instructor] Cập nhật câu hỏi")
def update_question(question_id: int, data: QuestionUpdate, db: DBSession, current_user: RequireInstructor):
    question = QuestionService(db).update(question_id=question_id, user=current_user, data=data)
    return APIResponse(message="Cập nhật câu hỏi thành công", data=QuestionResponse.model_validate(question))


@router.delete("/instructor/questions/{question_id}", summary="[Instructor] Xóa câu hỏi")
def delete_question(question_id: int, db: DBSession, current_user: RequireInstructor):
    QuestionService(db).delete(question_id=question_id, user=current_user)
    return APIResponse(message="Xóa câu hỏi thành công")


# ── Instructor: Quiz Management ───────────────────────────────────────────────
@router.get("/instructor/courses/{course_id}/quizzes", summary="[Instructor] Danh sách bài kiểm tra của khóa học")
def list_course_quizzes(course_id: int, db: DBSession, current_user: RequireInstructor):
    return APIResponse(data=QuizService(db).list_for_instructor(course_id, current_user))


@router.post("/instructor/quizzes", status_code=status.HTTP_201_CREATED, summary="[Instructor] Tạo bài kiểm tra")
def create_quiz(data: QuizCreate, db: DBSession, current_user: RequireInstructor):
    quiz = QuizService(db).create(data, current_user)
    return APIResponse(message="Tạo bài kiểm tra thành công", data=QuizResponse.model_validate(quiz))


@router.get("/instructor/quizzes/{quiz_id}", summary="[Instructor] Chi tiết bài kiểm tra (kèm đáp án)")
def get_quiz_detail(quiz_id: int, db: DBSession, current_user: RequireInstructor):
    return APIResponse(data=QuizService(db).get_detail(quiz_id, current_user))


@router.put("/instructor/quizzes/{quiz_id}", summary="[Instructor] Cập nhật bài kiểm tra")
def update_quiz(quiz_id: int, data: QuizUpdate, db: DBSession, current_user: RequireInstructor):
    quiz = QuizService(db).update(quiz_id=quiz_id, data=data, user=current_user)
    return APIResponse(message="Cập nhật bài kiểm tra thành công", data=QuizResponse.model_validate(quiz))


@router.delete("/instructor/quizzes/{quiz_id}", summary="[Instructor] Xóa bài kiểm tra")
def delete_quiz(quiz_id: int, db: DBSession, current_user: RequireInstructor):
    QuizService(db).delete(quiz_id, current_user)
    return APIResponse(message="Xóa bài kiểm tra thành công")


@router.get("/instructor/quizzes/{quiz_id}/attempts", summary="[Instructor] Kết quả làm bài của học viên")
def get_quiz_results(quiz_id: int, db: DBSession, current_user: RequireInstructor):
    return APIResponse(data=QuizService(db).get_quiz_results(quiz_id, current_user))


# ── Learner: Quiz Attempt ─────────────────────────────────────────────────────
@router.get("/courses/{course_id}/quizzes", summary="Danh sách bài kiểm tra của khóa học (học viên)")
def list_learner_quizzes(course_id: int, db: DBSession, current_user: CurrentUser):
    return APIResponse(data=QuizService(db).list_for_learner(course_id, current_user))


@router.post("/quizzes/{quiz_id}/start", summary="Bắt đầu (hoặc tiếp tục) lượt làm bài")
def start_quiz(quiz_id: int, db: DBSession, current_user: CurrentUser):
    return APIResponse(data=QuizService(db).start_quiz(quiz_id=quiz_id, user=current_user))


@router.post("/quizzes/attempts/{attempt_id}/submit", summary="Nộp bài và nhận kết quả chấm điểm")
def submit_quiz(attempt_id: int, data: QuizSubmitRequest, db: DBSession, current_user: CurrentUser):
    result = QuizService(db).submit_quiz(attempt_id=attempt_id, user=current_user, data=data)
    message = "Nộp bài thành công" if result.status == "SUBMITTED" else "Bài nộp quá thời gian quy định, lượt thi không được tính điểm"
    return APIResponse(message=message, data=result)


@router.get("/quizzes/attempts/{attempt_id}", summary="Xem lại kết quả một lượt thi đã nộp")
def get_attempt_result(attempt_id: int, db: DBSession, current_user: CurrentUser):
    return APIResponse(data=QuizService(db).get_attempt_result(attempt_id, current_user))


@router.get("/quizzes/{quiz_id}/attempts", summary="Lịch sử làm bài của tôi")
def get_my_attempts(quiz_id: int, db: DBSession, current_user: CurrentUser):
    return APIResponse(data=QuizService(db).get_quiz_attempts(quiz_id=quiz_id, user=current_user))
