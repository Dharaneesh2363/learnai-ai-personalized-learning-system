from datetime import datetime, timedelta
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, get_password_hash
from app.models.assessment import Question, QuestionDifficulty, QuestionType, Quiz, QuizAttempt
from app.models.study_plan import PlanType, StudyPlan, StudyPlanItem
from app.models.user import User, UserRole


def test_public_registration_privilege_escalation_blocked(client: TestClient, db_session):
    """Verify that an attacker attempting to register with role='admin' is forced to STUDENT."""
    hacker_email = f"hacker_{uuid.uuid4().hex[:6]}@evilcorp.io"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": hacker_email,
            "password": "Password123!",
            "full_name": "Dr. Hacker",
            "role": "admin"  # Attempting privilege escalation
        }
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["role"] == "student"

    # Verify directly in database
    created_user = db_session.query(User).filter(User.email == hacker_email).first()
    assert created_user is not None
    assert created_user.role == UserRole.STUDENT


def test_student_cannot_inspect_peer_quiz_attempt_idor(client: TestClient, db_session, test_user: User):
    """Verify IDOR prevention: student Alice cannot view student Bob's quiz attempt."""
    bob_email = f"bob_{uuid.uuid4().hex[:6]}@learnai.dev"
    bob = User(
        email=bob_email,
        hashed_password=get_password_hash("bobpass123"),
        full_name="Bob Smith",
        role=UserRole.STUDENT,
        is_active=True
    )
    db_session.add(bob)
    db_session.commit()
    db_session.refresh(bob)

    # Create dummy quiz and attempt owned by Bob
    quiz = Quiz(
        course_id=1,
        title="Security Test Quiz",
        is_adaptive=False,
        passing_score=70.0
    )
    db_session.add(quiz)
    db_session.commit()
    db_session.refresh(quiz)

    bob_attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=bob.id,
        score=85.0,
        max_score=100.0,
        percentage=85.0,
        passed=True,
        is_completed=True
    )
    db_session.add(bob_attempt)
    db_session.commit()
    db_session.refresh(bob_attempt)

    # Alice logs in
    token = create_access_token(subject=test_user.id, role=test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Alice tries to inspect Bob's attempt
    resp = client.get(f"/api/v1/quizzes/attempts/{bob_attempt.id}", headers=headers)
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]


def test_student_cannot_toggle_peer_study_plan_item(client: TestClient, db_session, test_user: User):
    """Verify that student Alice cannot modify or tamper with Bob's study plan items."""
    bob_email = f"bob_plan_{uuid.uuid4().hex[:6]}@learnai.dev"
    bob = User(
        email=bob_email,
        hashed_password=get_password_hash("bobpass123"),
        full_name="Bob Junior",
        role=UserRole.STUDENT,
        is_active=True
    )
    db_session.add(bob)
    db_session.commit()
    db_session.refresh(bob)

    now = datetime.utcnow()
    plan = StudyPlan(
        user_id=bob.id,
        title="Bob's Secret Plan",
        plan_type=PlanType.WEEKLY,
        start_date=now,
        end_date=now + timedelta(days=7),
        is_active=True
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    item = StudyPlanItem(
        study_plan_id=plan.id,
        day_of_week=1,
        title="Bob's Practice Goal",
        is_completed=False
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # Alice attempts to toggle Bob's plan item
    token = create_access_token(subject=test_user.id, role=test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(f"/api/v1/study-plans/items/{item.id}/toggle", headers=headers)
    assert resp.status_code == 403


def test_malformed_and_tampered_jwt_token_rejected(client: TestClient):
    """Verify that forged, malformed, or garbage JWT tokens are rejected with 401."""
    # Complete garbage token
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token-at-all"})
    assert resp.status_code == 401

    # Tampered signature token
    tampered = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.INVALID_SIGNATURE_HERE"
    resp2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert resp2.status_code == 401


def test_inactive_deactivated_account_blocked(client: TestClient, db_session):
    """Verify that disabled/deactivated accounts cannot authenticate or access endpoints."""
    inactive_email = f"disabled_{uuid.uuid4().hex[:6]}@learnai.dev"
    inactive_user = User(
        email=inactive_email,
        hashed_password=get_password_hash("password123"),
        full_name="Suspended Account",
        role=UserRole.STUDENT,
        is_active=False
    )
    db_session.add(inactive_user)
    db_session.commit()
    db_session.refresh(inactive_user)

    # Attempt login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": inactive_email, "password": "password123"}
    )
    assert login_resp.status_code == 403
    assert "deactivated" in login_resp.json()["detail"].lower()

    # Attempt using token for inactive user
    token = create_access_token(subject=inactive_user.id, role="student")
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 403
    assert "inactive" in me_resp.json()["detail"].lower()


def test_security_headers_present(client: TestClient):
    """Verify enterprise security headers are returned on all API responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
