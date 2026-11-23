import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:5432/erp_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-at-least-32-bytes-long")
os.environ.setdefault("FIRST_OWNER_EMAIL", "owner@example.com")
os.environ.setdefault("FIRST_OWNER_PASSWORD", "owner-password")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Role, User  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Each test starts from empty tables."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def make_user(db, email: str, role: Role, password: str = "password123") -> User:
    u = User(
        name=email.split("@")[0], email=email, role=role, password_hash=hash_password(password)
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def owner_headers(client):
    # The owner is created by the app on startup from FIRST_OWNER_* settings.
    return login(client, "owner@example.com", "owner-password")
