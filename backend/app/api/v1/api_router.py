"""API v1 – Main router aggregating all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, categories, courses, progress, quizzes, storage

api_router = APIRouter()

# Include all sub-routers with /api/v1 prefix (prefix set in main.py)
api_router.include_router(auth.router, tags=["Auth & Users"])
api_router.include_router(categories.router, tags=["Categories"])
api_router.include_router(courses.router, tags=["Courses & Content"])
api_router.include_router(progress.router, tags=["Enrollment & Progress"])
api_router.include_router(quizzes.router, tags=["Questions & Quizzes"])
api_router.include_router(storage.router, tags=["Storage"])
