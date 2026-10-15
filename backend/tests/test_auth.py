"""Authentication, profile and RBAC tests (SDD §4.1, §8.1-3)."""
from datetime import timedelta

from app.core.security import create_access_token, hash_password, verify_password
from tests.conftest import admin_token, auth_header, login, make_student, register


def test_password_hashing():
    hashed = hash_password("Password123@")
    assert hashed != "Password123@"
    assert verify_password("Password123@", hashed)
    assert not verify_password("wrong", hashed)


def test_register_login_me(client):
    data = register(client, "Student@Example.com")
    assert data["role"] == "STUDENT"
    assert data["email"] == "student@example.com"  # normalised

    r = client.post("/api/v1/auth/login", json={"email": "student@example.com", "password": "Password123@"})
    body = r.json()
    assert r.status_code == 200 and body["success"] is True
    assert body["data"]["token_type"] == "bearer"
    assert "refresh_token" in r.cookies  # HttpOnly cookie

    me = client.get("/api/v1/auth/me", headers=auth_header(body["data"]["access_token"]))
    assert me.json()["data"]["full_name"] == "Nguyễn Văn A"


def test_register_duplicate_and_weak_password(client):
    register(client, "a@example.com")
    r = client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "Password123@", "full_name": "AA"})
    assert r.status_code == 400 and r.json()["success"] is False

    r = client.post("/api/v1/auth/register", json={"email": "b@example.com", "password": "password", "full_name": "BB"})
    assert r.status_code == 400
    assert "chữ hoa" in r.json()["message"]


def test_login_wrong_password_and_locked_account(client):
    user = register(client, "a@example.com")
    assert client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "Nope123@"}).status_code == 401

    client.patch(f"/api/v1/admin/users/{user['user_id']}/status", json={"is_active": False}, headers=auth_header(admin_token(client)))
    r = client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "Password123@"})
    assert r.status_code == 401
    assert "khóa" in r.json()["message"]


def test_refresh_token_and_logout(client):
    register(client, "a@example.com")
    login(client, "a@example.com")  # TestClient keeps the cookie
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    assert r.json()["data"]["access_token"]

    client.post("/api/v1/auth/logout")
    client.cookies.clear()
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_refresh_token_cannot_be_used_as_access_token(client):
    register(client, "a@example.com")
    login(client, "a@example.com")
    refresh = client.cookies.get("refresh_token")
    assert client.get("/api/v1/auth/me", headers=auth_header(refresh)).status_code == 401


def test_expired_and_missing_token(client):
    user = register(client, "a@example.com")
    expired = create_access_token({"sub": str(user["user_id"]), "role": "STUDENT"}, expires_delta=timedelta(seconds=-1))
    assert client.get("/api/v1/auth/me", headers=auth_header(expired)).status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401


def test_update_profile_and_change_password(client):
    token = make_student(client)
    h = auth_header(token)
    r = client.put("/api/v1/auth/profile", json={"full_name": "Tên Mới"}, headers=h)
    assert r.json()["data"]["full_name"] == "Tên Mới"

    r = client.post("/api/v1/auth/change-password", json={"current_password": "sai", "new_password": "NewPass123"}, headers=h)
    assert r.status_code == 400
    r = client.post("/api/v1/auth/change-password", json={"current_password": "Password123@", "new_password": "NewPass123"}, headers=h)
    assert r.status_code == 200
    login(client, "student@example.com", "NewPass123")


def test_rbac_student_cannot_use_admin_or_instructor_api(client):
    h = auth_header(make_student(client))
    assert client.get("/api/v1/admin/users", headers=h).status_code == 403
    assert client.post("/api/v1/admin/courses/1/approve", headers=h).status_code == 403
    assert client.post("/api/v1/instructor/courses", json={"title": "abc", "category_id": 1}, headers=h).status_code == 403


def test_admin_user_management(client):
    register(client, "a@example.com")
    register(client, "b@example.com")
    h = auth_header(admin_token(client))
    r = client.get("/api/v1/admin/users", params={"role": "STUDENT", "page": 1, "limit": 1}, headers=h)
    data = r.json()["data"]
    assert data["total"] == 2 and data["pages"] == 2 and len(data["items"]) == 1

    r = client.get("/api/v1/admin/users", params={"search": "b@ex"}, headers=h)
    assert r.json()["data"]["total"] == 1


def test_admin_cannot_lock_or_demote_self(client):
    h = auth_header(admin_token(client))
    me = client.get("/api/v1/auth/me", headers=h).json()["data"]
    assert client.patch(f"/api/v1/admin/users/{me['id']}/status", json={"is_active": False}, headers=h).status_code == 400
    assert client.patch(f"/api/v1/admin/users/{me['id']}/role", json={"role": "STUDENT"}, headers=h).status_code == 400
