import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:5432/erp_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-at-least-32-bytes-long")
os.environ.setdefault("FIRST_OWNER_EMAIL", "owner@example.com")
os.environ.setdefault("FIRST_OWNER_PASSWORD", "owner-password")

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from alembic import command  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Role, User  # noqa: E402
from app.security import hash_password  # noqa: E402


def _reset_schema():
    """Drop everything (tables and enum types) and rebuild via the real migrations,
    so tests also exercise the migration files and the seeded chart of accounts."""
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    command.upgrade(cfg, "head")


@pytest.fixture(autouse=True)
def fresh_db():
    """Each test starts from freshly migrated, seeded tables."""
    _reset_schema()
    yield


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
