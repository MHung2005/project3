"""Service – Question & Quiz business logic."""
import json
from datetime import timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Question, Quiz, QuizAttempt
from app.repositories.quiz_repository import QuestionRepository, QuizAttemptRepository, QuizRepository
from app.repositories.progress_repository import EnrollmentRepository
from app.schemas.quiz import (
    QuestionCreate,
    QuestionReview,
    QuestionSafe,
    QuestionUpdate,
    QuizCreate,
    QuizStartResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizUpdate,
    QuestionOptionSafe,
)


class QuestionService:
    def __init__(self, db: Session):
        self.repo = QuestionRepository(db)

    def get_my_questions(self, instructor_id: int) -> list[Question]:
        return self.repo.get_by_instructor(instructor_id)

    def create(self, instructor_id: int, data: QuestionCreate) -> Question:
        return self.repo.create(
            instructor_id=instructor_id,
            content=data.content,
            question_type=data.question_type,
            explanation=data.explanation,
            options_data=data.options,
        )

    def update(self, question_id: int, instructor_id: int, data: QuestionUpdate) -> Question:
        question = self.repo.get_by_id(question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câu hỏi không tồn tại.")
        if question.instructor_id != instructor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền chỉnh sửa câu hỏi này.")
        update_data = data.model_dump(exclude_none=True)
        return self.repo.update(question, **update_data)

    def delete(self, question_id: int, instructor_id: int) -> None:
        question = self.repo.get_by_id(question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câu hỏi không tồn tại.")
        if question.instructor_id != instructor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xóa câu hỏi này.")
        self.repo.delete(question)


class QuizService:
    def __init__(self, db: Session):
        self.quiz_repo = QuizRepository(db)
        self.attempt_repo = QuizAttemptRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.question_repo = QuestionRepository(db)

    def create(self, data: QuizCreate) -> Quiz:
        # Validate all question IDs exist
        for qid in data.question_ids:
            if not self.question_repo.get_by_id(qid):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Câu hỏi ID {qid} không tồn tại.",
                )
        return self.quiz_repo.create(
            course_id=data.course_id,
            chapter_id=data.chapter_id,
            title=data.title,
            description=data.description,
            duration_minutes=data.duration_minutes,
            max_attempts=data.max_attempts,
            passing_score=data.passing_score,
            question_ids=data.question_ids,
        )

    def update(self, quiz_id: int, data: QuizUpdate) -> Quiz:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bài kiểm tra không tồn tại.")
        update_data = data.model_dump(exclude_none=True)
        question_ids = update_data.pop("question_ids", None)
        return self.quiz_repo.update(quiz, question_ids=question_ids, **update_data)

    def start_quiz(self, quiz_id: int, user_id: int) -> QuizStartResponse:
        """Begin a quiz attempt – checks attempt limits and returns safe questions."""
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bài kiểm tra không tồn tại.")

        # Verify enrollment
        enrollment = self.enrollment_repo.get_by_user_and_course(user_id, quiz.course_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn chưa đăng ký khóa học chứa bài kiểm tra này.",
            )

        # Check attempt limits
        attempt_count = self.attempt_repo.count_attempts(quiz_id, user_id)
        if attempt_count >= quiz.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn đã hết {quiz.max_attempts} lượt làm bài quy định.",
            )

        # Create new attempt
        attempt = self.attempt_repo.create(
            quiz_id=quiz_id,
            user_id=user_id,
            attempt_number=attempt_count + 1,
        )

        # Load questions WITHOUT is_correct / explanation (security!)
        questions = self.quiz_repo.get_questions_with_options(quiz_id)
        safe_questions = [
            QuestionSafe(
                id=q.id,
                content=q.content,
                question_type=q.question_type,
                options=[
                    QuestionOptionSafe(id=opt.id, content=opt.content, order_index=opt.order_index)
                    for opt in q.options
                ],
            )
            for q in questions
        ]

        return QuizStartResponse(
            attempt_id=attempt.id,
            attempt_number=attempt.attempt_number,
            duration_minutes=quiz.duration_minutes,
            questions=safe_questions,
        )

    def submit_quiz(self, attempt_id: int, user_id: int, data: QuizSubmitRequest) -> QuizSubmitResponse:
        """Grade the quiz server-side and return detailed review."""
        attempt = self.attempt_repo.get_by_id(attempt_id)
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lượt thi không tồn tại.")
        if attempt.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền nộp bài này.")
        if attempt.status != "IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lượt thi này đã được nộp hoặc đã hết thời gian.",
            )

        quiz = self.quiz_repo.get_by_id(attempt.quiz_id)
        questions = self.quiz_repo.get_questions_with_options(quiz.id)

        # Build answer lookup
        answer_lookup: dict[int, list[int]] = {
            ans.question_id: ans.selected_option_ids for ans in data.answers
        }

        # ── Grade ─────────────────────────────────────────────────────────────
        total_points = len(questions)  # each question worth equal weight
        earned_points = 0.0
        review: list[QuestionReview] = []

        for q in questions:
            correct_ids = sorted([opt.id for opt in q.options if opt.is_correct])
            selected_raw = answer_lookup.get(q.id, [])
            selected_ids = sorted(selected_raw)
            is_correct = selected_ids == correct_ids
            if is_correct:
                earned_points += 1.0

            review.append(
                QuestionReview(
                    question_id=q.id,
                    content=q.content,
                    user_selected=selected_raw,
                    correct_options=correct_ids,
                    is_correct=is_correct,
                    explanation=q.explanation,
                )
            )

        score = round((earned_points / total_points * 10) if total_points > 0 else 0.0, 2)
        is_passed = score >= quiz.passing_score

        # Persist answers
        answers_data = [
            {"question_id": ans.question_id, "selected_option_ids": ans.selected_option_ids}
            for ans in data.answers
        ]
        self.attempt_repo.submit(
            attempt=attempt,
            score=score,
            is_passed=is_passed,
            answers_data=answers_data,
        )

        return QuizSubmitResponse(
            score=score,
            is_passed=is_passed,
            passing_score=quiz.passing_score,
            submitted_at=attempt.submitted_at.isoformat() if attempt.submitted_at else "",
            review=review,
        )

    def get_quiz_attempts(self, quiz_id: int, user_id: int) -> list[QuizAttempt]:
        return self.attempt_repo.get_by_user_and_quiz(user_id, quiz_id)
