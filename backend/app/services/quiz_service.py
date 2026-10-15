"""Service – Question & Quiz business logic (SDD §4.4).

Security rule: questions sent to a learner during an attempt never contain
`is_correct` or `explanation`; grading happens 100% on the server.
"""
import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.utils import utc_now
from app.models.models import Question, Quiz, QuizAttempt, QuizQuestion, User
from app.repositories.course_repository import ChapterRepository
from app.repositories.progress_repository import EnrollmentRepository
from app.repositories.quiz_repository import QuestionRepository, QuizAttemptRepository, QuizRepository
from app.schemas.common import PaginatedResponse
from app.schemas.quiz import (
    QuestionCreate,
    QuestionOptionResponse,
    QuestionOptionSafe,
    QuestionResponse,
    QuestionReview,
    QuestionSafe,
    QuestionUpdate,
    QuizAttemptResponse,
    QuizAttemptStudentInfo,
    QuizCreate,
    QuizDetailResponse,
    QuizQuestionResponse,
    QuizResponse,
    QuizStartResponse,
    QuizStudentResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizUpdate,
    validate_options,
)
from app.services.permissions import (
    bad_request,
    can_manage_course,
    ensure_can_manage_course,
    forbidden,
    get_course_or_404,
    get_manageable_course,
    is_admin,
    not_found,
)
from app.services.progress_service import ProgressCalculator, summarize_attempts


class QuestionService:
    def __init__(self, db: Session):
        self.repo = QuestionRepository(db)

    def get_my_questions(
        self, user: User, page: int, limit: int, search: Optional[str] = None
    ) -> PaginatedResponse[QuestionResponse]:
        items, total = self.repo.get_by_instructor_paginated(user.id, page, limit, search)
        return PaginatedResponse[QuestionResponse].build(
            items=[QuestionResponse.model_validate(q) for q in items], total=total, page=page, limit=limit
        )

    def get_own(self, question_id: int, user: User) -> Question:
        question = self.repo.get_by_id(question_id)
        if not question:
            raise not_found("Câu hỏi không tồn tại.")
        if question.instructor_id != user.id and not is_admin(user):
            raise forbidden("Bạn không có quyền truy cập câu hỏi này.")
        return question

    def create(self, instructor_id: int, data: QuestionCreate) -> Question:
        return self.repo.create(
            instructor_id=instructor_id,
            content=data.content,
            question_type=data.question_type,
            explanation=data.explanation,
            options_data=data.options,
        )

    def update(self, question_id: int, user: User, data: QuestionUpdate) -> Question:
        question = self.get_own(question_id, user)
        update_data = data.model_dump(exclude_unset=True)
        # NOT NULL fields: an explicit null means "leave unchanged"
        for required in ("content", "question_type", "options"):
            if required in update_data and update_data[required] is None:
                update_data.pop(required)

        if "options" in update_data:
            if self.repo.has_been_answered(question_id):
                raise bad_request(
                    "Câu hỏi đã có học viên trả lời, không thể thay đổi các phương án. Hãy tạo câu hỏi mới."
                )
            update_data["options"] = data.options

        # Validate the final state (type + options) of the question
        final_type = update_data.get("question_type", question.question_type)
        final_options = data.options if data.options is not None else question.options
        try:
            validate_options(final_type, final_options)
        except ValueError as exc:
            raise bad_request(str(exc))
        return self.repo.update(question, **update_data)

    def delete(self, question_id: int, user: User) -> None:
        question = self.get_own(question_id, user)
        if self.repo.is_used_in_quiz(question_id):
            raise bad_request("Câu hỏi đang được sử dụng trong bài kiểm tra, không thể xóa.")
        self.repo.delete(question)


class QuizService:
    def __init__(self, db: Session):
        self.db = db
        self.quiz_repo = QuizRepository(db)
        self.attempt_repo = QuizAttemptRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _get_quiz(self, quiz_id: int) -> Quiz:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise not_found("Bài kiểm tra không tồn tại.")
        return quiz

    def _get_manageable_quiz(self, quiz_id: int, user: User) -> Quiz:
        quiz = self._get_quiz(quiz_id)
        ensure_can_manage_course(user, quiz.course, "Bạn không có quyền quản lý bài kiểm tra này.")
        return quiz

    def _validate_chapter(self, course_id: int, chapter_id: Optional[int]) -> None:
        if chapter_id is None:
            return
        chapter = ChapterRepository(self.db).get_by_id(chapter_id)
        if not chapter or chapter.course_id != course_id:
            raise bad_request("Chương học không thuộc khóa học này.")

    def _validate_questions(self, question_ids: list[int], user: User) -> None:
        questions = {q.id: q for q in QuestionRepository(self.db).get_by_ids(question_ids)}
        missing = [qid for qid in question_ids if qid not in questions]
        if missing:
            raise not_found(f"Câu hỏi ID {', '.join(map(str, missing))} không tồn tại.")
        if not is_admin(user):
            foreign = [qid for qid, q in questions.items() if q.instructor_id != user.id]
            if foreign:
                raise forbidden(f"Câu hỏi ID {', '.join(map(str, foreign))} không thuộc ngân hàng câu hỏi của bạn.")

    @staticmethod
    def _deadline(quiz: Quiz, attempt: QuizAttempt) -> datetime:
        return attempt.started_at + timedelta(minutes=quiz.duration_minutes)

    def _is_expired(self, quiz: Quiz, attempt: QuizAttempt) -> bool:
        grace = timedelta(seconds=settings.QUIZ_SUBMIT_GRACE_SECONDS)
        return utc_now() > self._deadline(quiz, attempt) + grace

    # ── Instructor: CRUD ──────────────────────────────────────────────────────
    def create(self, data: QuizCreate, user: User) -> Quiz:
        course = get_manageable_course(
            self.db, data.course_id, user, "Bạn không có quyền tạo bài kiểm tra cho khóa học này."
        )
        self._validate_chapter(course.id, data.chapter_id)
        self._validate_questions(data.question_ids, user)
        quiz = self.quiz_repo.create(
            course_id=data.course_id,
            chapter_id=data.chapter_id,
            title=data.title,
            description=data.description,
            duration_minutes=data.duration_minutes,
            max_attempts=data.max_attempts,
            passing_score=data.passing_score,
            question_ids=data.question_ids,
        )
        ProgressCalculator(self.db).recalculate_course(course.id)
        return quiz

    def update(self, quiz_id: int, data: QuizUpdate, user: User) -> Quiz:
        quiz = self._get_manageable_quiz(quiz_id, user)
        update_data = data.model_dump(exclude_unset=True)
        # NOT NULL fields: an explicit null means "leave unchanged"
        for required in ("title", "duration_minutes", "max_attempts", "passing_score", "question_ids"):
            if required in update_data and update_data[required] is None:
                update_data.pop(required)
        question_ids = update_data.pop("question_ids", None)
        if "chapter_id" in update_data:
            self._validate_chapter(quiz.course_id, update_data["chapter_id"])
        if question_ids is not None:
            if self.attempt_repo.get_by_quiz(quiz_id):
                raise bad_request("Bài kiểm tra đã có lượt làm bài, không thể thay đổi danh sách câu hỏi.")
            self._validate_questions(question_ids, user)
        return self.quiz_repo.update(quiz, question_ids=question_ids, **update_data)

    def delete(self, quiz_id: int, user: User) -> None:
        quiz = self._get_manageable_quiz(quiz_id, user)
        if self.attempt_repo.get_by_quiz(quiz_id):
            raise bad_request("Bài kiểm tra đã có học viên làm bài, không thể xóa.")
        course_id = quiz.course_id
        self.quiz_repo.delete(quiz)
        ProgressCalculator(self.db).recalculate_course(course_id)

    def get_detail(self, quiz_id: int, user: User) -> QuizDetailResponse:
        self._get_manageable_quiz(quiz_id, user)
        quiz = self.quiz_repo.get_detail(quiz_id)
        return QuizDetailResponse(
            **QuizResponse.model_validate(quiz).model_dump(),
            questions=[QuizQuestionResponse.model_validate(qq) for qq in quiz.quiz_questions],
        )

    def list_for_instructor(self, course_id: int, user: User) -> list[QuizResponse]:
        get_manageable_course(self.db, course_id, user)
        return [QuizResponse.model_validate(q) for q in self.quiz_repo.get_by_course(course_id)]

    def get_quiz_results(self, quiz_id: int, user: User) -> list[QuizAttemptStudentInfo]:
        self._get_manageable_quiz(quiz_id, user)
        return [
            QuizAttemptStudentInfo(
                **QuizAttemptResponse.model_validate(a).model_dump(),
                full_name=a.user.full_name,
                email=a.user.email,
            )
            for a in self.attempt_repo.get_by_quiz(quiz_id)
        ]

    # ── Learner ───────────────────────────────────────────────────────────────
    def _ensure_learner_access(self, quiz: Quiz, user: User) -> None:
        if can_manage_course(user, quiz.course):
            return
        if not self.enrollment_repo.get_by_user_and_course(user.id, quiz.course_id):
            raise forbidden("Bạn chưa đăng ký khóa học chứa bài kiểm tra này.")

    def list_for_learner(self, course_id: int, user: User) -> list[QuizStudentResponse]:
        course = get_course_or_404(self.db, course_id)
        if not can_manage_course(user, course) and not self.enrollment_repo.get_by_user_and_course(user.id, course_id):
            raise forbidden("Bạn chưa đăng ký khóa học này.")
        quizzes = self.quiz_repo.get_by_course(course_id)
        quiz_ids = [q.id for q in quizzes]
        counts = self.quiz_repo.count_questions(quiz_ids)
        attempts = self.attempt_repo.get_by_user_and_quizzes(user.id, quiz_ids)
        return [
            QuizStudentResponse(
                **QuizResponse.model_validate(q).model_dump(),
                question_count=counts.get(q.id, 0),
                **summarize_attempts([a for a in attempts if a.quiz_id == q.id]),
            )
            for q in quizzes
        ]

    def start_quiz(self, quiz_id: int, user: User) -> QuizStartResponse:
        """Begin (or resume) a quiz attempt and return questions without answers."""
        quiz = self._get_quiz(quiz_id)
        self._ensure_learner_access(quiz, user)

        quiz_questions = self.quiz_repo.get_quiz_questions(quiz_id)
        if not quiz_questions:
            raise bad_request("Bài kiểm tra chưa có câu hỏi.")

        # Resume an unfinished attempt (e.g. page reload) instead of burning a new one
        attempt = self.attempt_repo.get_in_progress(quiz_id, user.id)
        if attempt is not None and self._is_expired(quiz, attempt):
            self.attempt_repo.mark_timeout(attempt)
            attempt = None

        if attempt is None:
            attempt_count = self.attempt_repo.count_attempts(quiz_id, user.id)
            if attempt_count >= quiz.max_attempts:
                raise forbidden(f"Đã hết số lượt làm bài quy định ({quiz.max_attempts} lượt).")
            attempt = self.attempt_repo.create(quiz_id=quiz_id, user_id=user.id, attempt_number=attempt_count + 1)

        safe_questions = [
            QuestionSafe(
                id=qq.question.id,
                content=qq.question.content,
                question_type=qq.question.question_type,
                options=[QuestionOptionSafe.model_validate(opt) for opt in qq.question.options],
            )
            for qq in quiz_questions
        ]
        return QuizStartResponse(
            attempt_id=attempt.id,
            attempt_number=attempt.attempt_number,
            duration_minutes=quiz.duration_minutes,
            started_at=attempt.started_at,
            expires_at=self._deadline(quiz, attempt),
            questions=safe_questions,
        )

    @staticmethod
    def _grade(quiz_questions: list[QuizQuestion], answers: dict[int, list[int]]) -> tuple[float, list[QuestionReview]]:
        """Return (score on a 10-point scale, per-question review)."""
        total_points = sum(qq.point for qq in quiz_questions)
        earned = 0.0
        review: list[QuestionReview] = []
        for qq in quiz_questions:
            q = qq.question
            correct_ids = sorted(opt.id for opt in q.options if opt.is_correct)
            selected = sorted(set(answers.get(q.id, [])))
            is_correct = selected == correct_ids
            if is_correct:
                earned += qq.point
            review.append(
                QuestionReview(
                    question_id=q.id,
                    content=q.content,
                    point=qq.point,
                    options=[QuestionOptionResponse.model_validate(o) for o in q.options],
                    user_selected=selected,
                    correct_options=correct_ids,
                    is_correct=is_correct,
                    explanation=q.explanation,
                )
            )
        score = round(earned / total_points * 10, 2) if total_points > 0 else 0.0
        return score, review

    def submit_quiz(self, attempt_id: int, user: User, data: QuizSubmitRequest) -> QuizSubmitResponse:
        """Grade the quiz server-side and return a detailed review."""
        attempt = self.attempt_repo.get_by_id(attempt_id)
        if not attempt:
            raise not_found("Lượt thi không tồn tại.")
        if attempt.user_id != user.id:
            raise forbidden("Bạn không có quyền nộp bài này.")
        if attempt.status != "IN_PROGRESS":
            raise bad_request("Lượt thi này đã được nộp hoặc đã hết thời gian.")

        quiz = self._get_quiz(attempt.quiz_id)
        quiz_questions = self.quiz_repo.get_quiz_questions(quiz.id)

        # Keep only answers to questions of this quiz, with option ids belonging to that question
        valid_options = {qq.question.id: {o.id for o in qq.question.options} for qq in quiz_questions}
        answers: dict[int, list[int]] = {}
        for ans in data.answers:
            if ans.question_id in valid_options:
                answers[ans.question_id] = [oid for oid in ans.selected_option_ids if oid in valid_options[ans.question_id]]

        if self._is_expired(quiz, attempt):
            # Submitted after time limit + grace period: the attempt counts with score 0
            attempt_status = "TIMEOUT"
            _, review = self._grade(quiz_questions, {})
            score = 0.0
        else:
            attempt_status = "SUBMITTED"
            score, review = self._grade(quiz_questions, answers)
        is_passed = attempt_status == "SUBMITTED" and score >= quiz.passing_score

        self.attempt_repo.submit(
            attempt=attempt,
            score=score,
            is_passed=is_passed,
            answers_data=[{"question_id": qid, "selected_option_ids": ids} for qid, ids in answers.items()],
            status=attempt_status,
        )

        if is_passed:
            enrollment = self.enrollment_repo.get_by_user_and_course(user.id, quiz.course_id)
            if enrollment:
                ProgressCalculator(self.db).recalculate(enrollment)

        return QuizSubmitResponse(
            attempt_id=attempt.id,
            status=attempt.status,
            score=score,
            is_passed=is_passed,
            passing_score=quiz.passing_score,
            submitted_at=attempt.submitted_at,
            review=review,
        )

    def get_attempt_result(self, attempt_id: int, user: User) -> QuizSubmitResponse:
        """Re-display the review of a finished attempt (owner, or course manager)."""
        attempt = self.attempt_repo.get_with_answers(attempt_id)
        if not attempt:
            raise not_found("Lượt thi không tồn tại.")
        quiz = self._get_quiz(attempt.quiz_id)
        if attempt.user_id != user.id and not can_manage_course(user, quiz.course):
            raise forbidden("Bạn không có quyền xem lượt thi này.")
        if attempt.status == "IN_PROGRESS":
            raise bad_request("Lượt thi chưa được nộp.")

        answers = {a.question_id: json.loads(a.selected_option_ids or "[]") for a in attempt.answers}
        _, review = self._grade(self.quiz_repo.get_quiz_questions(quiz.id), answers)
        return QuizSubmitResponse(
            attempt_id=attempt.id,
            status=attempt.status,
            score=attempt.score or 0.0,
            is_passed=attempt.is_passed,
            passing_score=quiz.passing_score,
            submitted_at=attempt.submitted_at,
            review=review,
        )

    def get_quiz_attempts(self, quiz_id: int, user: User) -> list[QuizAttemptResponse]:
        quiz = self._get_quiz(quiz_id)
        self._ensure_learner_access(quiz, user)
        return [QuizAttemptResponse.model_validate(a) for a in self.attempt_repo.get_by_user_and_quiz(user.id, quiz_id)]
