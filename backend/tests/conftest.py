"""Test fixtures – runs the whole API against a throw-away SQLite database.

Environment variables must be set before `app` is imported, because settings and
the SQLAlchemy engine are created at import time.
"""
import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="elearning-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test.db')}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["DEBUG"] = "false"
os.environ["FIRST_ADMIN_EMAIL"] = "admin@example.com"
os.environ["FIRST_ADMIN_PASSWORD"] = "Admin123@"
os.environ["DB_CONNECT_RETRIES"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

ADMIN = ("admin@example.com", "Admin123@")


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # runs lifespan: create tables + seed admin
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    with SessionLocal() as session:
        yield session


# ── Helpers ───────────────────────────────────────────────────────────────────
def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(client: TestClient, email: str, password: str = "Password123@", full_name: str = "Nguyễn Văn A") -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": full_name})
    assert r.status_code == 201, r.text
    return r.json()["data"]


def login(client: TestClient, email: str, password: str = "Password123@") -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["data"]["access_token"]


def admin_token(client: TestClient) -> str:
    return login(client, *ADMIN)


def make_instructor(client: TestClient, email: str = "teacher@example.com") -> str:
    user = register(client, email, full_name="Giảng Viên")
    r = client.patch(
        f"/api/v1/admin/users/{user['user_id']}/role",
        json={"role": "INSTRUCTOR"},
        headers=auth_header(admin_token(client)),
    )
    assert r.status_code == 200, r.text
    return login(client, email)


def make_student(client: TestClient, email: str = "student@example.com") -> str:
    register(client, email, full_name="Lê Mạnh Hùng")
    return login(client, email)


def create_category(client: TestClient, slug: str = "lap-trinh-web") -> int:
    r = client.post(
        "/api/v1/admin/categories",
        json={"name": f"Danh mục {slug}", "slug": slug},
        headers=auth_header(admin_token(client)),
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


def published_course(client: TestClient, teacher: str, video_duration: int = 600) -> dict:
    """Create a course with 1 chapter, 1 video lesson + 1 document lesson, and get it approved."""
    cat_id = create_category(client)
    h = auth_header(teacher)
    course = client.post(
        "/api/v1/instructor/courses",
        json={"title": "Lập trình Web hiện đại", "category_id": cat_id, "description": "Khóa học thực chiến"},
        headers=h,
    ).json()["data"]
    chapter = client.post(f"/api/v1/instructor/courses/{course['id']}/chapters", json={"title": "Chương 1"}, headers=h).json()["data"]
    video = client.post(
        f"/api/v1/instructor/chapters/{chapter['id']}/lessons",
        json={
            "title": "Bài 1: Giới thiệu",
            "lesson_type": "VIDEO",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "duration_seconds": video_duration,
            "is_free_preview": False,
        },
        headers=h,
    ).json()["data"]
    doc = client.post(
        f"/api/v1/instructor/chapters/{chapter['id']}/lessons",
        json={"title": "Bài 2: Tài liệu", "lesson_type": "DOCUMENT", "document_url": "http://localhost:9000/materials/abc.pdf"},
        headers=h,
    ).json()["data"]
    assert client.post(f"/api/v1/instructor/courses/{course['id']}/submit-review", headers=h).status_code == 200
    r = client.post(f"/api/v1/admin/courses/{course['id']}/approve", headers=auth_header(admin_token(client)))
    assert r.status_code == 200, r.text
    return {"course": course, "chapter": chapter, "video": video, "doc": doc, "category_id": cat_id}
