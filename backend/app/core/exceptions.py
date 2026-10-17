"""Application (domain) exceptions.

Services raise these instead of `fastapi.HTTPException`, so the business layer does not
depend on the web framework. `app.main` registers a handler that turns every `AppError`
into the same JSON shape FastAPI uses for HTTPException: `{"detail": "..."}`.
"""
from typing import Optional


class AppError(Exception):
    status_code: int = 400

    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(detail)
        self.detail = detail
        self.headers = headers


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401

    def __init__(self, detail: str):
        super().__init__(detail, headers={"WWW-Authenticate": "Bearer"})


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ServiceUnavailableError(AppError):
    status_code = 503
