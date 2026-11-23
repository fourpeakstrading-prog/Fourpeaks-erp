from app.models import Role
from tests.conftest import login, make_user


def test_owner_can_create_user_and_it_is_audited(client, owner_headers):
    r = client.post(
        "/users",
        headers=owner_headers,
        json={
            "name": "Aisha",
            "email": "Aisha@example.com",
            "password": "password123",
            "role": "sales",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "aisha@example.com"
    assert body["role"] == "sales"

    log = client.get("/audit", headers=owner_headers, params={"table_name": "users"}).json()
    assert len(log) == 1
    assert log[0]["action"] == "create"
    assert log[0]["record_id"] == body["id"]
    assert "password_hash" not in log[0]["after"]


def test_duplicate_email_is_refused(client, owner_headers):
    payload = {"name": "A", "email": "a@example.com", "password": "password123", "role": "viewer"}
    assert client.post("/users", headers=owner_headers, json=payload).status_code == 201
    assert client.post("/users", headers=owner_headers, json=payload).status_code == 409


def test_non_owner_cannot_manage_users(client, db):
    make_user(db, "acct@example.com", Role.accountant)
    headers = login(client, "acct@example.com", "password123")
    assert client.get("/users", headers=headers).status_code == 403
    r = client.post(
        "/users",
        headers=headers,
        json={
            "name": "X",
            "email": "x@example.com",
            "password": "password123",
            "role": "viewer",
        },
    )
    assert r.status_code == 403


def test_update_records_before_and_after(client, owner_headers, db):
    u = make_user(db, "stores@example.com", Role.stores)
    r = client.patch(f"/users/{u.id}", headers=owner_headers, json={"role": "hr"})
    assert r.status_code == 200
    assert r.json()["role"] == "hr"

    log = client.get("/audit", headers=owner_headers, params={"record_id": str(u.id)}).json()
    assert log[0]["action"] == "update"
    assert log[0]["before"]["role"] == "stores"
    assert log[0]["after"]["role"] == "hr"


def test_owner_cannot_deactivate_self(client, owner_headers):
    me = client.get("/auth/me", headers=owner_headers).json()
    r = client.patch(f"/users/{me['id']}", headers=owner_headers, json={"active": False})
    assert r.status_code == 400


def test_viewer_cannot_read_audit_log_but_accountant_can(client, db):
    make_user(db, "viewer@example.com", Role.viewer)
    make_user(db, "acct@example.com", Role.accountant)
    assert (
        client.get("/audit", headers=login(client, "viewer@example.com", "password123")).status_code
        == 403
    )
    assert (
        client.get("/audit", headers=login(client, "acct@example.com", "password123")).status_code
        == 200
    )


def test_settings_default_and_owner_update(client, owner_headers, db):
    make_user(db, "sales@example.com", Role.sales)
    sales = login(client, "sales@example.com", "password123")

    s = client.get("/settings", headers=sales).json()
    assert s["currency"] == "OMR" and s["currency_decimals"] == 3 and s["vat_enabled"] is False

    assert client.patch("/settings", headers=sales, json={"vat_enabled": True}).status_code == 403

    r = client.patch(
        "/settings",
        headers=owner_headers,
        json={"company_name": "Al Jabal Trading LLC", "cr_number": "1234567"},
    )
    assert r.status_code == 200
    assert r.json()["company_name"] == "Al Jabal Trading LLC"
