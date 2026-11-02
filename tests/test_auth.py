"""Unit tests for authentication and JWT workflows."""
import json


def test_login_success(client):
    """Test successful login with valid credentials."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin@123",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "admin@test.com"


def test_login_invalid_password(client):
    """Test login failure with incorrect password."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "WrongPassword",
    })
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["success"] is False


def test_get_current_user_profile(client, admin_headers):
    """Test authenticated profile retrieval with JWT header."""
    resp = client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "admin@test.com"


def test_unauthorized_access(client):
    """Test that protected endpoint blocks request without token."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
