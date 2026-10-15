"""Course authoring, moderation, categories and storage tests (SDD §4.2, §4.5)."""
from app.core.utils import extract_youtube_id
from app.services.storage_service import storage_service
from tests.conftest import (
    admin_token,
    auth_header,
    create_category,
    make_instructor,
    make_student,
    published_course,
)


def test_extract_youtube_id():
    assert extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_id("https://youtu.be/dQw4w9WgXcQ?t=10") == "dQw4w9WgXcQ"
    assert extract_youtube_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_id("https://vimeo.com/123") is None


def test_category_crud_and_delete_guard(client):
    h = auth_header(admin_token(client))
    cat_id = create_category(client, "ai")
    assert client.post("/api/v1/admin/categories", json={"name": "Khác", "slug": "ai"}, headers=h).status_code == 400
    assert client.post("/api/v1/admin/categories", json={"name": "Khác", "slug": "Bad Slug"}, headers=h).status_code == 400

    r = client.put(f"/api/v1/admin/categories/{cat_id}", json={"description": "Trí tuệ nhân tạo"}, headers=h)
    assert r.json()["data"]["description"] == "Trí tuệ nhân tạo"
    assert len(client.get("/api/v1/categories").json()["data"]) == 1

    teacher = make_instructor(client)
    client.post("/api/v1/instructor/courses", json={"title": "Khóa AI", "category_id": cat_id}, headers=auth_header(teacher))
    r = client.delete(f"/api/v1/admin/categories/{cat_id}", headers=h)
    assert r.status_code == 400  # course depends on it


def test_course_review_workflow(client):
    teacher = make_instructor(client)
    th = auth_header(teacher)
    ah = auth_header(admin_token(client))
    cat_id = create_category(client)

    course = client.post("/api/v1/instructor/courses", json={"title": "Next.js & FastAPI", "category_id": cat_id}, headers=th)
    assert course.status_code == 201
    course = course.json()["data"]
    assert course["status"] == "DRAFT"

    # Cannot submit an empty course
    r = client.post(f"/api/v1/instructor/courses/{course['id']}/submit-review", headers=th)
    assert r.status_code == 400 and "ít nhất 1 bài học" in r.json()["message"]

    chapter = client.post(f"/api/v1/instructor/courses/{course['id']}/chapters", json={"title": "Chương 1"}, headers=th).json()["data"]
    assert chapter["order_index"] == 1

    bad = client.post(
        f"/api/v1/instructor/chapters/{chapter['id']}/lessons",
        json={"title": "Video", "lesson_type": "VIDEO", "video_url": "https://example.com/video.mp4"},
        headers=th,
    )
    assert bad.status_code == 400 and "YouTube" in bad.json()["message"]

    lesson = client.post(
        f"/api/v1/instructor/chapters/{chapter['id']}/lessons",
        json={"title": "Video", "lesson_type": "VIDEO", "video_url": "https://youtu.be/dQw4w9WgXcQ", "duration_seconds": 300},
        headers=th,
    ).json()["data"]
    assert lesson["youtube_video_id"] == "dQw4w9WgXcQ"

    assert client.post(f"/api/v1/instructor/courses/{course['id']}/submit-review", headers=th).json()["data"]["status"] == "PENDING"
    # Content is frozen while pending
    assert client.put(f"/api/v1/instructor/courses/{course['id']}", json={"title": "Đổi tên"}, headers=th).status_code == 400

    pending = client.get("/api/v1/admin/courses", params={"status": "PENDING"}, headers=ah).json()["data"]
    assert pending["total"] == 1

    r = client.post(f"/api/v1/admin/courses/{course['id']}/reject", json={"reason": "Cần bổ sung tài liệu"}, headers=ah)
    assert r.json()["data"]["status"] == "REJECTED"
    assert r.json()["data"]["rejection_reason"] == "Cần bổ sung tài liệu"

    # Unpublished courses are hidden from the public
    assert client.get(f"/api/v1/courses/{course['id']}").status_code == 404
    assert client.get(f"/api/v1/courses/{course['id']}", headers=th).status_code == 200

    client.post(f"/api/v1/instructor/courses/{course['id']}/submit-review", headers=th)
    r = client.post(f"/api/v1/admin/courses/{course['id']}/approve", headers=ah)
    assert r.json()["data"]["status"] == "PUBLISHED"
    assert r.json()["data"]["rejection_reason"] is None

    listing = client.get("/api/v1/courses", params={"search": "next"}).json()["data"]
    assert listing["total"] == 1
    assert listing["items"][0]["instructor"]["full_name"] == "Giảng Viên"
    assert "email" not in listing["items"][0]["instructor"]


def test_instructor_cannot_edit_others_course(client):
    owner = make_instructor(client, "owner@example.com")
    other = make_instructor(client, "other@example.com")
    cat_id = create_category(client)
    course = client.post("/api/v1/instructor/courses", json={"title": "Khóa A", "category_id": cat_id}, headers=auth_header(owner)).json()["data"]
    r = client.put(f"/api/v1/instructor/courses/{course['id']}", json={"title": "Hack"}, headers=auth_header(other))
    assert r.status_code == 403
    r = client.post(f"/api/v1/instructor/courses/{course['id']}/chapters", json={"title": "Hack"}, headers=auth_header(other))
    assert r.status_code == 403


def test_public_detail_hides_paid_content(client):
    teacher = make_instructor(client)
    data = published_course(client, teacher)
    course_id = data["course"]["id"]

    detail = client.get(f"/api/v1/courses/{course_id}").json()["data"]
    lessons = detail["chapters"][0]["lessons"]
    assert all(ls["is_locked"] and ls["video_url"] is None for ls in lessons)
    assert detail["total_lessons"] == 2 and detail["total_duration_seconds"] == 600

    student = make_student(client)
    sh = auth_header(student)
    assert client.get(f"/api/v1/lessons/{data['video']['id']}", headers=sh).status_code == 403

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=sh)
    detail = client.get(f"/api/v1/courses/{course_id}", headers=sh).json()["data"]
    assert detail["is_enrolled"] is True
    assert detail["chapters"][0]["lessons"][0]["video_url"]

    # Private material is served through a presigned URL
    doc = client.get(f"/api/v1/lessons/{data['doc']['id']}", headers=sh).json()["data"]
    assert "X-Amz-Signature" in doc["document_url"]


def test_delete_lesson_with_progress(client):
    teacher = make_instructor(client)
    data = published_course(client, teacher)
    student = make_student(client)
    sh = auth_header(student)
    client.post(f"/api/v1/courses/{data['course']['id']}/enroll", headers=sh)
    client.post(f"/api/v1/lessons/{data['doc']['id']}/complete", json={}, headers=sh)

    r = client.delete(f"/api/v1/instructor/lessons/{data['doc']['id']}", headers=auth_header(teacher))
    assert r.status_code == 200
    progress = client.get(f"/api/v1/courses/{data['course']['id']}/progress", headers=sh).json()["data"]
    assert progress["total_lessons"] == 1 and progress["completed_lessons"] == 0


def test_instructor_enroll_student_and_view_progress(client):
    teacher = make_instructor(client)
    th = auth_header(teacher)
    data = published_course(client, teacher)
    make_student(client, "s2@example.com")

    r = client.post(f"/api/v1/instructor/courses/{data['course']['id']}/enroll-student", json={"student_email": "s2@example.com"}, headers=th)
    assert r.status_code == 201
    r = client.post(f"/api/v1/instructor/courses/{data['course']['id']}/enroll-student", json={"student_email": "s2@example.com"}, headers=th)
    assert r.status_code == 400
    r = client.post(f"/api/v1/instructor/courses/{data['course']['id']}/enroll-student", json={"student_email": "none@example.com"}, headers=th)
    assert r.status_code == 404

    students = client.get(f"/api/v1/instructor/courses/{data['course']['id']}/students", headers=th).json()["data"]
    assert len(students) == 1 and students[0]["total_lessons"] == 2


class _FakeMinio:
    def __init__(self):
        self.objects = {}

    def bucket_exists(self, bucket):
        return True

    def set_bucket_policy(self, bucket, policy):
        pass

    def put_object(self, bucket_name, object_name, data, length, content_type):
        self.objects[(bucket_name, object_name)] = data.read()


def test_storage_upload(client, monkeypatch):
    fake = _FakeMinio()
    monkeypatch.setattr(storage_service, "_client", fake)
    th = auth_header(make_instructor(client))

    r = client.post(
        "/api/v1/storage/upload",
        files={"file": ("tai-lieu.pdf", b"%PDF-1.4 test", "application/pdf")},
        data={"bucket": "materials"},
        headers=th,
    )
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["file_url"].startswith("http://localhost:9000/materials/") and body["file_size"] == 13
    assert len(fake.objects) == 1

    r = client.post("/api/v1/storage/upload", files={"file": ("virus.exe", b"MZ", "application/x-msdownload")}, headers=th)
    assert r.status_code == 400

    # Students may only upload their own avatar
    sh = auth_header(make_student(client))
    assert client.post("/api/v1/storage/upload", files={"file": ("a.pdf", b"x", "application/pdf")}, headers=sh).status_code == 403
    r = client.post("/api/v1/storage/upload-avatar", files={"file": ("me.png", b"\x89PNG", "image/png")}, headers=sh)
    assert r.status_code == 200
    assert r.json()["data"]["user"]["avatar_url"].startswith("http://localhost:9000/avatars/")
