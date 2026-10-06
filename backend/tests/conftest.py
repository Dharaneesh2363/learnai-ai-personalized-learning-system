import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.rollback()
        db_session.close()


@pytest.fixture
def db_session(db):
    return db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def student_user(db):
    user = db.query(User).filter(User.email == "student@learnai.dev").first()
    return user


@pytest.fixture
def test_user(student_user):
    return student_user


@pytest.fixture
def admin_user(db):
    user = db.query(User).filter(User.email == "admin@learnai.dev").first()
    return user


@pytest.fixture
def student_auth_headers(student_user):
    token = create_access_token(subject=student_user.id, role=student_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user):
    token = create_access_token(subject=admin_user.id, role=admin_user.role.value)
    return {"Authorization": f"Bearer {token}"}
