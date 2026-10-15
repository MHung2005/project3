"""Repository – Question, Quiz, QuizAttempt, QuizAttemptAnswer data access."""
import json
from typing import Optional

from sqlalchemy import case, func, true
from sqlalchemy.orm import Session, selectinload

from app.core.utils import utc_now
from app.models.models import (
    Question,
    QuestionOption,
    Quiz,
    QuizAttempt,
    QuizAttemptAnswer,
    QuizQuestion,
)


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, question_id: int) -> Optional[Question]:
        return (
            self.db.query(Question)
            .options(selectinload(Question.options))
            .filter(Question.id == question_id)
            .first()
        )

    def get_by_ids(self, question_ids: list[int]) -> list[Question]:
        if not question_ids:
            return []
        return self.db.query(Question).filter(Question.id.in_(question_ids)).all()

    def get_by_instructor_paginated(
        self, instructor_id: Optional[int], page: int, limit: int, search: Optional[str] = None
    ) -> tuple[list[Question], int]:
        query = self.db.query(Question)
        if instructor_id is not None:
            query = query.filter(Question.instructor_id == instructor_id)
        if search:
            query = query.filter(Question.content.ilike(f"%{search}%"))
        total = query.count()
        items = (
            query.options(selectinload(Question.options))
            .order_by(Question.created_at.desc(), Question.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return items, total

    def create(self, instructor_id: int, content: str, question_type: str, explanation: Optional[str], options_data: list) -> Question:
        question = Question(
            instructor_id=instructor_id,
            content=content,
            question_type=question_type,
            explanation=explanation,
        )
        for opt in options_data:
            question.options.append(
                QuestionOption(content=opt.content, is_correct=opt.is_correct, order_index=opt.order_index)
            )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def update(self, question: Question, **kwargs) -> Question:
        options_data = kwargs.pop("options", None)
        for key, value in kwargs.items():
            if hasattr(question, key):
                setattr(question, key, value)
        if options_data is not None:
            # Replace all options (delete-orphan cascade removes the old rows)
            question.options.clear()
            self.db.flush()
            for opt in options_data:
                question.options.append(
                    QuestionOption(content=opt.content, is_correct=opt.is_correct, order_index=opt.order_index)
                )
        self.db.commit()
        self.db.refresh(question)
        return question

    def delete(self, question: Question) -> None:
        self.db.delete(question)
        self.db.commit()

    def is_used_in_quiz(self, question_id: int) -> bool:
        return self.db.query(QuizQuestion.id).filter(QuizQuestion.question_id == question_id).first() is not None

    def has_been_answered(self, question_id: int) -> bool:
        return (
            self.db.query(QuizAttemptAnswer.id).filter(QuizAttemptAnswer.question_id == question_id).first()
            is not None
        )


class QuizRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, quiz_id: int) -> Optional[Quiz]:
        return self.db.get(Quiz, quiz_id)

    def get_detail(self, quiz_id: int) -> Optional[Quiz]:
        return (
            self.db.query(Quiz)
            .options(
                selectinload(Quiz.quiz_questions)
                .selectinload(QuizQuestion.question)
                .selectinload(Question.options)
            )
            .filter(Quiz.id == quiz_id)
            .first()
        )

    def get_by_course(self, course_id: int) -> list[Quiz]:
        return (
            self.db.query(Quiz)
            .filter(Quiz.course_id == course_id)
            # Chapter quizzes first, final exams (chapter_id NULL) last – portable across SQL dialects
            .order_by(case((Quiz.chapter_id.is_(None), 1), else_=0), Quiz.chapter_id, Quiz.id)
            .all()
        )

    def count_questions(self, quiz_ids: list[int]) -> dict[int, int]:
        if not quiz_ids:
            return {}
        rows = (
            self.db.query(QuizQuestion.quiz_id, func.count(QuizQuestion.id))
            .filter(QuizQuestion.quiz_id.in_(quiz_ids))
            .group_by(QuizQuestion.quiz_id)
            .all()
        )
        return dict(rows)

    def create(
        self,
        course_id: int,
        chapter_id: Optional[int],
        title: str,
        description: Optional[str],
        duration_minutes: int,
        max_attempts: int,
        passing_score: float,
        question_ids: list[int],
    ) -> Quiz:
        quiz = Quiz(
            course_id=course_id,
            chapter_id=chapter_id,
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            max_attempts=max_attempts,
            passing_score=passing_score,
        )
        for idx, qid in enumerate(question_ids, start=1):
            quiz.quiz_questions.append(QuizQuestion(question_id=qid, order_index=idx, point=1.0))
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def update(self, quiz: Quiz, question_ids: Optional[list[int]] = None, **kwargs) -> Quiz:
        for key, value in kwargs.items():
            if hasattr(quiz, key):
                setattr(quiz, key, value)
        if question_ids is not None:
            quiz.quiz_questions.clear()
            self.db.flush()
            for idx, qid in enumerate(question_ids, start=1):
                quiz.quiz_questions.append(QuizQuestion(question_id=qid, order_index=idx, point=1.0))
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def delete(self, quiz: Quiz) -> None:
        self.db.delete(quiz)
        self.db.commit()

    def get_quiz_questions(self, quiz_id: int) -> list[QuizQuestion]:
        """Load the quiz's question links (with question + options), in exam order."""
        return (
            self.db.query(QuizQuestion)
            .options(selectinload(QuizQuestion.question).selectinload(Question.options))
            .filter(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.order_index, QuizQuestion.id)
            .all()
        )


class QuizAttemptRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_attempts(self, quiz_id: int, user_id: int) -> int:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == user_id)
            .count()
        )

    def get_by_id(self, attempt_id: int) -> Optional[QuizAttempt]:
        return self.db.get(QuizAttempt, attempt_id)

    def get_with_answers(self, attempt_id: int) -> Optional[QuizAttempt]:
        return (
            self.db.query(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .filter(QuizAttempt.id == attempt_id)
            .first()
        )

    def get_by_user_and_quiz(self, user_id: int, quiz_id: int) -> list[QuizAttempt]:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.attempt_number)
            .all()
        )

    def get_by_user_and_quizzes(self, user_id: int, quiz_ids: list[int]) -> list[QuizAttempt]:
        if not quiz_ids:
            return []
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id.in_(quiz_ids))
            .all()
        )

    def get_by_quiz(self, quiz_id: int) -> list[QuizAttempt]:
        return (
            self.db.query(QuizAttempt)
            .options(selectinload(QuizAttempt.user))
            .filter(QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.started_at.desc())
            .all()
        )

    def get_in_progress(self, quiz_id: int, user_id: int) -> Optional[QuizAttempt]:
        return (
            self.db.query(QuizAttempt)
            .filter(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == user_id,
                QuizAttempt.status == "IN_PROGRESS",
            )
            .order_by(QuizAttempt.attempt_number.desc())
            .first()
        )

    def count_passed_quizzes(self, user_id: int, quiz_ids: list[int]) -> int:
        """Number of distinct quizzes (among quiz_ids) the user has passed at least once."""
        if not quiz_ids:
            return 0
        return (
            self.db.query(func.count(func.distinct(QuizAttempt.quiz_id)))
            .filter(
                QuizAttempt.user_id == user_id,
                QuizAttempt.quiz_id.in_(quiz_ids),
                QuizAttempt.is_passed == true(),
            )
            .scalar()
            or 0
        )

    def create(self, quiz_id: int, user_id: int, attempt_number: int) -> QuizAttempt:
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            attempt_number=attempt_number,
            status="IN_PROGRESS",
            started_at=utc_now(),
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def mark_timeout(self, attempt: QuizAttempt) -> QuizAttempt:
        """Close an abandoned attempt with score 0."""
        attempt.status = "TIMEOUT"
        attempt.score = 0.0
        attempt.is_passed = False
        attempt.submitted_at = utc_now()
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def submit(
        self,
        attempt: QuizAttempt,
        score: float,
        is_passed: bool,
        answers_data: list[dict],
        status: str = "SUBMITTED",
    ) -> QuizAttempt:
        attempt.score = score
        attempt.is_passed = is_passed
        attempt.status = status
        attempt.submitted_at = utc_now()
        for ans in answers_data:
            attempt.answers.append(
                QuizAttemptAnswer(
                    question_id=ans["question_id"],
                    selected_option_ids=json.dumps(sorted(ans["selected_option_ids"])),
                )
            )
        self.db.commit()
        self.db.refresh(attempt)
        return attempt
