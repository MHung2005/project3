"""ORM models (SDD §3.2).

Importing this package registers every table on `Base.metadata`.
"""
from app.models.category import Category
from app.models.course import Chapter, Course, Lesson
from app.models.enrollment import Enrollment, LessonProgress
from app.models.quiz import Question, QuestionOption, Quiz, QuizAttempt, QuizAttemptAnswer, QuizQuestion
from app.models.user import User

__all__ = [
    "Category",
    "Chapter",
    "Course",
    "Enrollment",
    "Lesson",
    "LessonProgress",
    "Question",
    "QuestionOption",
    "Quiz",
    "QuizAttempt",
    "QuizAttemptAnswer",
    "QuizQuestion",
    "User",
]
