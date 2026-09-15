import uuid
import jwt

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.db import SessionLocal
from backend.app.models.user import User
from ..app.core.config import settings
from backend.app.main import app


client = TestClient(app)


def delete_user_by_email(email: str):
    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is not None:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_register_creates_user():
    email = f"register-{uuid.uuid4()}@example.com"

    payload = {
        "email": email,
        "password": "test1234"
    }

    try:
        response = client.post(
            "/api/v1/auth/register",
            json=payload
        )

        assert response.status_code == 201

        result = response.json()

        assert result["email"] == email
        assert result["timezone"] == "UTC"
        assert result["currency"] == "USD"
        assert "id" in result
        assert "created_at" in result
        assert "password" not in result
        assert "password_hash" not in result

    finally:
        delete_user_by_email(email)


def test_register_rejects_duplicate_email():
    email = f"duplicate-{uuid.uuid4()}@example.com"

    payload = {
        "email": email,
        "password": "test1234"
    }

    try:
        first_response = client.post(
            "/api/v1/auth/register",
            json=payload
        )

        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/auth/register",
            json=payload
        )

        assert second_response.status_code == 409
        assert second_response.json()["detail"] == (
            "User already exists"
        )

    finally:
        delete_user_by_email(email)


def test_get_current_user_with_valid_token():
    email = f"me-{uuid.uuid4()}@example.com"
    password = "test1234"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert me_response.status_code == 200

    response_data = me_response.json()

    assert response_data["email"] == email
    assert "id" in response_data
    assert "password" not in response_data
    assert "password_hash" not in response_data


def test_get_current_user_without_token_returns_401():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_current_user_with_invalid_token_returns_401():
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401


def test_get_current_user_with_expired_token_returns_401():
    expired_token = jwt.encode(
        {
            "sub": "test-user-id",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}"
        },
    )

    assert response.status_code == 401
