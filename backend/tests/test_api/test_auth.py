import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass",
            "roles": "user",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["username"] == "testuser"


def test_login_success(client: TestClient):
    # First register
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpass",
            "roles": "user",
        },
    )
    # Then login
    response = client.post(
        "/api/v1/auth/login", data={"username": "testuser2", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/v1/auth/login", data={"username": "nonexistent", "password": "wrongpass"}
    )
    assert response.status_code == 400
    assert "Incorrect username or password" in response.json()["detail"]


def test_register_duplicate_username(client: TestClient):
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "dup1@example.com",
            "password": "pass",
            "roles": "user",
        },
    )
    # Try to register again
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "dup2@example.com",
            "password": "pass",
            "roles": "user",
        },
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_admin_login_success(client: TestClient, admin_token):
    assert admin_token is not None


def test_unauthorized_access_without_token(client: TestClient):
    response = client.get("/api/v1/files")
    assert response.status_code == 401
