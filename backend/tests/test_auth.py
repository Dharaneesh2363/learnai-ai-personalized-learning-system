import pytest
from app.core.security import get_password_hash, verify_password


def test_password_hashing():
    pwd = "supersecretpassword123"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@learnai.dev", "password": "student123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "student@learnai.dev"
    assert data["user"]["role"] == "student"


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@learnai.dev", "password": "wrongpassword!"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_me_profile(client, student_auth_headers):
    response = client.get("/api/v1/auth/me", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "student@learnai.dev"
    assert data["full_name"] == "Alex Chen (Demo Student)"


def test_rbac_guard_blocks_student_from_admin_route(client, student_auth_headers):
    # Student should get 403 Forbidden on admin endpoint
    response = client.get("/api/v1/admin/students", headers=student_auth_headers)
    assert response.status_code == 403


def test_rbac_guard_allows_admin(client, admin_auth_headers):
    # Admin should get 200 OK
    response = client.get("/api/v1/admin/students", headers=admin_auth_headers)
    assert response.status_code == 200
    students = response.json()
    assert len(students) >= 1
