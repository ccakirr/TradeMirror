import uuid

import pytest

from ..app.db import SessionLocal
from ..app.models.user import User
from ..app.schemas.user import UserCreate, UserResponse
from ..app.services.user import create_user


def test_create_user():
    db = SessionLocal()
    email = f"test-{uuid.uuid4()}@gmail.com"

    try:
        user_data = UserCreate(
            email=email,
            password="test1234"
        )

        response = create_user(db, user_data)

        assert isinstance(response, UserResponse)
        assert response.email == email
        assert response.id is not None
        assert not hasattr(response, "password")
        assert not hasattr(response, "password_hash")
    finally:
        created_user = db.get(User, response.id)

        if created_user is not None:
            db.delete(created_user)
            db.commit()

        db.close()


def test_create_user_rejects_duplicate_email():
    db = SessionLocal()
    email = f"duplicate-{uuid.uuid4()}@gmail.com"

    try:
        first_user = create_user(
            db,
            UserCreate(
                email=email,
                password="test1234"
            )
        )

        with pytest.raises(
            ValueError,
            match="User already exists"
        ):
            create_user(
                db,
                UserCreate(
                    email=email,
                    password="test1234"
                )
            )
    finally:
        created_user = db.get(User, first_user.id)

        if created_user is not None:
            db.delete(created_user)
            db.commit()

        db.close()
