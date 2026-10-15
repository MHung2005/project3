"""Pydantic schemas – Questions & Quizzes."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Question Option Schemas ───────────────────────────────────────────────────
class QuestionOptionCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_correct: bool = False
    order_index: int = Field(default=1, ge=1)


class QuestionOptionResponse(BaseModel):
    id: int
    question_id: int
    content: str
    is_correct: bool
    order_index: int

    model_config = {"from_attributes": True}


class QuestionOptionSafe(BaseModel):
    """Option response WITHOUT is_correct – safe to send to students during quiz."""
    id: int
    content: str
    order_index: int

    model_config = {"from_attributes": True}


def validate_options(question_type: str, options: List[QuestionOptionCreate]) -> None:
    correct = sum(1 for o in options if o.is_correct)
    if correct == 0:
        raise ValueError("Câu hỏi phải có ít nhất 1 đáp án đúng.")
    if question_type == "SINGLE_CHOICE" and correct != 1:
        raise ValueError("Câu hỏi SINGLE_CHOICE phải có đúng 1 đáp án đúng.")


# ── Question Schemas ──────────────────────────────────────────────────────────
class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=5)
    question_type: str = Field(default="SINGLE_CHOICE", pattern="^(SINGLE_CHOICE|MULTIPLE_CHOICE)$")
    explanation: Optional[str] = None
    options: List[QuestionOptionCreate] = Field(..., min_length=2, max_length=10)

    @model_validator(mode="after")
    def check_options(self) -> "QuestionCreate":
        validate_options(self.question_type, self.options)
        return self


class QuestionUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=5)
    question_type: Optional[str] = Field(None, pattern="^(SINGLE_CHOICE|MULTIPLE_CHOICE)$")
    explanation: Optional[str] = None
    options: Optional[List[QuestionOptionCreate]] = Field(None, min_length=2, max_length=10)


class QuestionResponse(BaseModel):
    id: int
    instructor_id: int
    content: str
    question_type: str
    explanation: Optional[str] = None
    created_at: datetime
    options: List[QuestionOptionResponse] = []

    model_config = {"from_attributes": True}


class QuestionSafe(BaseModel):
    """Question response without answer info – for active quiz sessions."""
    id: int
    content: str
    question_type: str
    options: List[QuestionOptionSafe] = []

    model_config = {"from_attributes": True}


# ── Quiz Schemas ──────────────────────────────────────────────────────────────
def _unique_ids(v: Optional[List[int]]) -> Optional[List[int]]:
    if v is not None and len(set(v)) != len(v):
        raise ValueError("Danh sách question_ids không được trùng lặp.")
    return v


class QuizCreate(BaseModel):
    course_id: int = Field(..., gt=0)
    chapter_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(default=15, ge=1, le=300)
    max_attempts: int = Field(default=3, ge=1)
    passing_score: float = Field(default=8.0, ge=0.0, le=10.0)
    question_ids: List[int] = Field(..., min_length=1)

    @field_validator("question_ids")
    @classmethod
    def check_unique_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        return _unique_ids(v)


class QuizUpdate(BaseModel):
    chapter_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=300)
    max_attempts: Optional[int] = Field(None, ge=1)
    passing_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    question_ids: Optional[List[int]] = Field(None, min_length=1)

    @field_validator("question_ids")
    @classmethod
    def check_unique_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        return _unique_ids(v)


class QuizResponse(BaseModel):
    id: int
    course_id: int
    chapter_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    duration_minutes: int
    max_attempts: int
    passing_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizQuestionResponse(BaseModel):
    order_index: int
    point: float
    question: QuestionResponse

    model_config = {"from_attributes": True}


class QuizDetailResponse(QuizResponse):
    """Full quiz with answers – instructor only."""
    questions: List[QuizQuestionResponse] = []


class QuizStudentResponse(QuizResponse):
    """Quiz info for a learner (no question content)."""
    question_count: int
    attempts_used: int
    best_score: Optional[float] = None
    is_passed: bool = False


# ── Quiz Attempt Schemas ──────────────────────────────────────────────────────
class QuizStartResponse(BaseModel):
    attempt_id: int
    attempt_number: int
    duration_minutes: int
    started_at: datetime
    expires_at: datetime
    questions: List[QuestionSafe]


class AnswerSubmit(BaseModel):
    question_id: int
    selected_option_ids: List[int] = []


class QuizSubmitRequest(BaseModel):
    answers: List[AnswerSubmit] = []


class QuestionReview(BaseModel):
    question_id: int
    content: str
    point: float
    options: List[QuestionOptionResponse] = []
    user_selected: List[int]
    correct_options: List[int]
    is_correct: bool
    explanation: Optional[str] = None


class QuizSubmitResponse(BaseModel):
    attempt_id: int
    status: str
    score: float
    is_passed: bool
    passing_score: float
    submitted_at: datetime
    review: List[QuestionReview]


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    attempt_number: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    score: Optional[float] = None
    is_passed: bool
    status: str

    model_config = {"from_attributes": True}


class QuizAttemptStudentInfo(QuizAttemptResponse):
    """Attempt row with learner identity – instructor result view."""
    full_name: str
    email: str
