"""API Router – Questions & Quizzes."""
from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession, RequireInstructor
from app.schemas.quiz import (
    QuestionCreate,
    QuestionUpdate,
    QuizCreate,
    QuizSubmitRequest,
    QuizUpdate,
)
from app.schemas.user import APIResponse
from app.services.quiz_service import QuestionService, QuizService

router = APIRouter()


# ── Instructor: Question Bank ─────────────────────────────────────────────────
@router.get("/instructor/questions", summary="[Instructor] Ngân hàng câu hỏi của tôi")
def get_my_questions(db: DBSession, current_user: RequireInstructor):
    svc = QuestionService(db)
    questions = svc.get_my_questions(current_user.id)
    return APIResponse(data=questions)


@router.post("/instructor/questions", status_code=status.HTTP_201_CREATED, summary="[Instructor] Tạo câu hỏi mới")
def create_question(data: QuestionCreate, db: DBSession, current_user: RequireInstructor):
    svc = QuestionService(db)
    question = svc.create(instructor_id=current_user.id, data=data)
    return APIResponse(message="Tạo câu hỏi thành công", data=question)


@router.put("/instructor/questions/{question_id}", summary="[Instructor] Cập nhật câu hỏi")
def update_question(question_id: int, data: QuestionUpdate, db: DBSession, current_user: RequireInstructor):
    svc = QuestionService(db)
    question = svc.update(question_id=question_id, instructor_id=current_user.id, data=data)
    return APIResponse(message="Cập nhật câu hỏi thành công", data=question)


@router.delete("/instructor/questions/{question_id}", summary="[Instructor] Xóa câu hỏi")
def delete_question(question_id: int, db: DBSession, current_user: RequireInstructor):
    svc = QuestionService(db)
    svc.delete(question_id=question_id, instructor_id=current_user.id)
    return APIResponse(message="Xóa câu hỏi thành công")


# ── Instructor: Quiz Management ───────────────────────────────────────────────
@router.post("/instructor/quizzes", status_code=status.HTTP_201_CREATED, summary="[Instructor] Tạo bài kiểm tra")
def create_quiz(data: QuizCreate, db: DBSession, current_user: RequireInstructor):
    svc = QuizService(db)
    quiz = svc.create(data)
    return APIResponse(message="Tạo bài kiểm tra thành công", data=quiz)


@router.put("/instructor/quizzes/{quiz_id}", summary="[Instructor] Cập nhật bài kiểm tra")
def update_quiz(quiz_id: int, data: QuizUpdate, db: DBSession, current_user: RequireInstructor):
    svc = QuizService(db)
    quiz = svc.update(quiz_id=quiz_id, data=data)
    return APIResponse(message="Cập nhật bài kiểm tra thành công", data=quiz)


# ── Student: Quiz Attempt ─────────────────────────────────────────────────────
@router.post("/quizzes/{quiz_id}/start", summary="[Student] Bắt đầu làm bài kiểm tra")
def start_quiz(quiz_id: int, db: DBSession, current_user: CurrentUser):
    svc = QuizService(db)
    result = svc.start_quiz(quiz_id=quiz_id, user_id=current_user.id)
    return APIResponse(data=result)


@router.post("/quizzes/attempts/{attempt_id}/submit", summary="[Student] Nộp bài kiểm tra")
def submit_quiz(attempt_id: int, data: QuizSubmitRequest, db: DBSession, current_user: CurrentUser):
    svc = QuizService(db)
    result = svc.submit_quiz(attempt_id=attempt_id, user_id=current_user.id, data=data)
    return APIResponse(message="Nộp bài thành công", data=result)


@router.get("/quizzes/{quiz_id}/attempts", summary="Lịch sử làm bài của tôi")
def get_my_attempts(quiz_id: int, db: DBSession, current_user: CurrentUser):
    svc = QuizService(db)
    attempts = svc.get_quiz_attempts(quiz_id=quiz_id, user_id=current_user.id)
    return APIResponse(data=attempts)
