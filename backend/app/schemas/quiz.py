"""Pydantic schemas – Questions & Quizzes."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


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


# ── Question Schemas ──────────────────────────────────────────────────────────
class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=5)
    question_type: str = Field(default="SINGLE_CHOICE", pattern="^(SINGLE_CHOICE|MULTIPLE_CHOICE)$")
    explanation: Optional[str] = None
    options: List[QuestionOptionCreate] = Field(..., min_length=2)


class QuestionUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=5)
    question_type: Optional[str] = Field(None, pattern="^(SINGLE_CHOICE|MULTIPLE_CHOICE)$")
    explanation: Optional[str] = None
    options: Optional[List[QuestionOptionCreate]] = None


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
class QuizCreate(BaseModel):
    course_id: int = Field(..., gt=0)
    chapter_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(default=15, ge=1, le=300)
    max_attempts: int = Field(default=3, ge=1)
    passing_score: float = Field(default=8.0, ge=0.0, le=10.0)
    question_ids: List[int] = Field(..., min_length=1)


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=300)
    max_attempts: Optional[int] = Field(None, ge=1)
    passing_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    question_ids: Optional[List[int]] = None


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


# ── Quiz Attempt Schemas ──────────────────────────────────────────────────────
class QuizStartResponse(BaseModel):
    attempt_id: int
    attempt_number: int
    duration_minutes: int
    questions: List[QuestionSafe]


class AnswerSubmit(BaseModel):
    question_id: int
    selected_option_ids: List[int]


class QuizSubmitRequest(BaseModel):
    answers: List[AnswerSubmit]


class QuestionReview(BaseModel):
    question_id: int
    content: str
    user_selected: List[int]
    correct_options: List[int]
    is_correct: bool
    explanation: Optional[str] = None


class QuizSubmitResponse(BaseModel):
    score: float
    is_passed: bool
    passing_score: float
    submitted_at: str
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
