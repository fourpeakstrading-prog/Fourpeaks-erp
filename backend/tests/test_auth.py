from app.models import Role
from tests.conftest import make_user


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_first_owner_is_created_on_startup(client, owner_headers):
    me = client.get("/auth/me", headers=owner_headers).json()
    assert me["email"] == "owner@example.com"
    assert me["role"] == "owner"


def test_wrong_password_is_rejected(client):
    r = client.post("/auth/login", data={"username": "owner@example.com", "password": "nope"})
    assert r.status_code == 401


def test_login_is_case_insensitive_on_email(client):
    r = client.post(
        "/auth/login", data={"username": "OWNER@example.com", "password": "owner-password"}
    )
    assert r.status_code == 200


def test_protected_route_needs_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_deactivated_user_cannot_log_in(client, db):
    u = make_user(db, "sales@example.com", Role.sales)
    u.active = False
    db.commit()
    r = client.post("/auth/login", data={"username": u.email, "password": "password123"})
    assert r.status_code == 401
