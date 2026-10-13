"""Repository – Question, Quiz, QuizAttempt, QuizAttemptAnswer data access."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, selectinload

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

    def get_by_instructor(self, instructor_id: int) -> list[Question]:
        return (
            self.db.query(Question)
            .options(selectinload(Question.options))
            .filter(Question.instructor_id == instructor_id)
            .order_by(Question.created_at.desc())
            .all()
        )

    def create(self, instructor_id: int, content: str, question_type: str, explanation: Optional[str], options_data: list) -> Question:
        question = Question(
            instructor_id=instructor_id,
            content=content,
            question_type=question_type,
            explanation=explanation,
        )
        self.db.add(question)
        self.db.flush()  # get question.id without committing
        for opt in options_data:
            option = QuestionOption(
                question_id=question.id,
                content=opt.content,
                is_correct=opt.is_correct,
                order_index=opt.order_index,
            )
            self.db.add(option)
        self.db.commit()
        self.db.refresh(question)
        return question

    def update(self, question: Question, **kwargs) -> Question:
        options_data = kwargs.pop("options", None)
        for key, value in kwargs.items():
            if hasattr(question, key):
                setattr(question, key, value)
        if options_data is not None:
            # Replace all options
            for opt in question.options:
                self.db.delete(opt)
            self.db.flush()
            for opt in options_data:
                option = QuestionOption(
                    question_id=question.id,
                    content=opt.content,
                    is_correct=opt.is_correct,
                    order_index=opt.order_index,
                )
                self.db.add(option)
        self.db.commit()
        self.db.refresh(question)
        return question

    def delete(self, question: Question) -> None:
        self.db.delete(question)
        self.db.commit()

    def get_options_map(self, question_ids: list[int]) -> dict[int, list[QuestionOption]]:
        """Return {question_id: [options]} for a set of question IDs."""
        options = (
            self.db.query(QuestionOption)
            .filter(QuestionOption.question_id.in_(question_ids))
            .all()
        )
        result: dict[int, list[QuestionOption]] = {}
        for opt in options:
            result.setdefault(opt.question_id, []).append(opt)
        return result


class QuizRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, quiz_id: int) -> Optional[Quiz]:
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def get_by_course(self, course_id: int) -> list[Quiz]:
        return self.db.query(Quiz).filter(Quiz.course_id == course_id).all()

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
        self.db.add(quiz)
        self.db.flush()
        for idx, qid in enumerate(question_ids, start=1):
            qq = QuizQuestion(quiz_id=quiz.id, question_id=qid, order_index=idx, point=1.0)
            self.db.add(qq)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def update(self, quiz: Quiz, question_ids: Optional[list[int]] = None, **kwargs) -> Quiz:
        for key, value in kwargs.items():
            if hasattr(quiz, key):
                setattr(quiz, key, value)
        if question_ids is not None:
            for qq in quiz.quiz_questions:
                self.db.delete(qq)
            self.db.flush()
            for idx, qid in enumerate(question_ids, start=1):
                self.db.add(QuizQuestion(quiz_id=quiz.id, question_id=qid, order_index=idx, point=1.0))
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def delete(self, quiz: Quiz) -> None:
        self.db.delete(quiz)
        self.db.commit()

    def get_questions_with_options(self, quiz_id: int) -> list[Question]:
        """Load all questions (with options) for a quiz."""
        quiz_questions = (
            self.db.query(QuizQuestion)
            .options(
                selectinload(QuizQuestion.question).selectinload(Question.options)
            )
            .filter(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.order_index)
            .all()
        )
        return [qq.question for qq in quiz_questions]


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
        return self.db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()

    def get_by_user_and_quiz(self, user_id: int, quiz_id: int) -> list[QuizAttempt]:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.attempt_number)
            .all()
        )

    def create(self, quiz_id: int, user_id: int, attempt_number: int) -> QuizAttempt:
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            attempt_number=attempt_number,
            status="IN_PROGRESS",
        )
        self.db.add(attempt)
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
        attempt.submitted_at = datetime.now(timezone.utc)
        self.db.flush()
        for ans in answers_data:
            answer = QuizAttemptAnswer(
                attempt_id=attempt.id,
                question_id=ans["question_id"],
                selected_option_ids=str(ans["selected_option_ids"]),
            )
            self.db.add(answer)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt
