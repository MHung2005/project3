"""API v1 – Main router aggregating all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, categories, courses, lessons, progress, quizzes, storage, users

api_router = APIRouter()

api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(users.router, tags=["Admin – Users"])
api_router.include_router(categories.router, tags=["Categories"])
api_router.include_router(courses.router, tags=["Courses & Chapters"])
api_router.include_router(lessons.router, tags=["Lessons"])
api_router.include_router(progress.router, tags=["Enrollment & Progress"])
api_router.include_router(quizzes.router, tags=["Questions & Quizzes"])
api_router.include_router(storage.router, tags=["Storage"])
