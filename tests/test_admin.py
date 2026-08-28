import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


@pytest.fixture(scope="module")
def client():
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def admin_headers(client):
    db = SessionLocal()
    email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    admin_user = User(
        name="Test Admin",
        email=email,
        hashed_password=get_password_hash("AdminPass123!"),
        role="admin",
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    db.close()

    res = client.post("/auth/login", json={"email": email, "password": "AdminPass123!"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def regular_user_headers(client):
    email = f"reguser_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/auth/signup", json={"name": "Regular User", "email": email, "password": "UserPass123!"})
    res = client.post("/auth/login", json={"email": email, "password": "UserPass123!"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_regular_user_cannot_access_admin_endpoints(client, regular_user_headers):
    """Non-admin users must receive 403 Forbidden."""
    res = client.get("/admin/users", headers=regular_user_headers)
    assert res.status_code == 403
    assert "Admin privileges required" in res.json()["detail"]


def test_admin_list_users(client, admin_headers):
    """Admin can list all registered users."""
    res = client.get("/admin/users", headers=admin_headers)
    assert res.status_code == 200
    users = res.json()
    assert isinstance(users, list)
    assert len(users) >= 1
    first = users[0]
    assert "id" in first
    assert "email" in first
    assert "role" in first
    assert "is_active" in first


def test_admin_suspend_and_restore_user(client, admin_headers):
    """Admin can suspend and subsequently reactivate a user account."""
    # Create target user
    target_email = f"target_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/auth/signup", json={"name": "Target User", "email": target_email, "password": "TargetPass123!"})
    login = client.post("/auth/login", json={"email": target_email, "password": "TargetPass123!"})
    target_id = login.json()["user"]["id"]
    target_token = login.json()["access_token"]
    target_headers = {"Authorization": f"Bearer {target_token}"}

    # Suspend user
    suspend_res = client.patch(f"/admin/users/{target_id}/suspend", headers=admin_headers)
    assert suspend_res.status_code == 200
    assert suspend_res.json()["is_active"] is False

    # Suspended user must be blocked on protected endpoints
    blocked_res = client.get("/documents", headers=target_headers)
    assert blocked_res.status_code == 403
    assert "Inactive or suspended" in blocked_res.json()["detail"]

    # Reactivate user
    restore_res = client.patch(f"/admin/users/{target_id}/suspend", headers=admin_headers)
    assert restore_res.status_code == 200
    assert restore_res.json()["is_active"] is True

    # User can now access endpoints again
    unblocked_res = client.get("/documents", headers=target_headers)
    assert unblocked_res.status_code == 200


def test_admin_delete_user(client, admin_headers):
    """Admin can permanently delete a user and their cascaded data."""
    del_email = f"todelete_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/auth/signup", json={"name": "Delete Me", "email": del_email, "password": "DeletePass123!"})
    login = client.post("/auth/login", json={"email": del_email, "password": "DeletePass123!"})
    del_id = login.json()["user"]["id"]

    del_res = client.delete(f"/admin/users/{del_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["detail"]

    # Verify user cannot log in
    check_login = client.post("/auth/login", json={"email": del_email, "password": "DeletePass123!"})
    assert check_login.status_code == 401
