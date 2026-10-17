"""
E-Learning Platform

"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import SessionLocal
from app.db.utils import create_all_tables, wait_for_database
from app.services.auth_service import seed_first_admin


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown logic."""
    wait_for_database()
    create_all_tables()
    with SessionLocal() as db:
        seed_first_admin(db)
    yield


# ── Application Factory ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Nền tảng học trực tuyến (E-Learning Platform)

Hệ thống API hỗ trợ:
- **Student**: Đăng ký khóa học, theo dõi tiến độ, làm bài kiểm tra
- **Instructor**: Quản lý khóa học, bài học, ngân hàng câu hỏi
- **Admin**: Quản lý người dùng, phê duyệt khóa học
""",
    contact={"name": "Lê Mạnh Hùng – MSSV: 20235096"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Map service-layer errors to HTTP responses (same shape as HTTPException)."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


app.include_router(api_router, prefix="/api/v1")
