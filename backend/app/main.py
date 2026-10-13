"""
ELearning Platform – FastAPI Application Entry Point
====================================================
Bootstraps the FastAPI app, registers all middleware, includes all routers,
and sets up database tables on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.database import create_all_tables


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown logic."""
    # Startup: create tables if they don't exist
    create_all_tables()
    print(f"✅  Database tables ensured. App '{settings.APP_NAME}' is ready.")
    yield
    # Shutdown: clean up resources (if any)
    print("🛑  Application shutting down.")


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

### Xác thực
Sử dụng `Bearer <access_token>` trong header `Authorization`.
""",
    contact={
        "name": "Lê Mạnh Hùng – MSSV: 20235096",
        "email": "hung@example.com",
    },
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

# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        import traceback
        traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Lỗi máy chủ nội bộ. Vui lòng thử lại sau.",
            "data": None,
            "error": str(exc) if settings.DEBUG else "Internal Server Error",
        },
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"], summary="Kiểm tra trạng thái hệ thống")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"], include_in_schema=False)
def root():
    return {"message": f"Welcome to {settings.APP_NAME} API. Visit /docs for documentation."}
