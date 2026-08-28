import uuid
import pytest
from app.core.security import decode_access_token


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_signup_flow(client):
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Test User",
        "email": unique_email,
        "password": "SecurePassword123!",
    }
    
    # 1. Successful signup
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == unique_email
    assert data["role"] == "user"
    assert "hashed_password" not in data
    assert "id" in data

    # 2. Duplicate email rejected
    dup_res = client.post("/auth/signup", json=payload)
    assert dup_res.status_code == 400
    assert "already registered" in dup_res.json()["detail"]


def test_login_flow(client):
    unique_email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    password = "CorrectPassword123!"
    
    # Sign up user
    client.post("/auth/signup", json={
        "name": "Login User",
        "email": unique_email,
        "password": password,
    })

    # 1. Invalid password
    bad_login = client.post("/auth/login", json={
        "email": unique_email,
        "password": "WrongPassword!",
    })
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]

    # 2. Valid password
    good_login = client.post("/auth/login", json={
        "email": unique_email,
        "password": password,
    })
    assert good_login.status_code == 200
    auth_data = good_login.json()
    assert "access_token" in auth_data
    assert auth_data["token_type"] == "bearer"
    assert auth_data["user"]["email"] == unique_email
    assert auth_data["user"]["role"] == "user"

    token = auth_data["access_token"]
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == auth_data["user"]["id"]
    assert decoded["role"] == "user"

    # 3. Access /auth/me with Bearer token
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email


def test_logout(client):
    res = client.post("/auth/logout")
    assert res.status_code == 200
    assert res.json()["detail"] == "Logged out successfully"
