import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.db import SessionLocal
from backend.app.main import app
from backend.app.models.user import User


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
