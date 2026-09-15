import uuid

import pytest

from backend.app.db import SessionLocal
from backend.app.models.user import User
from backend.app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse
)
from backend.app.services.user import (
    authenticate_user,
    create_user
)


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_user(db):
    password = "test1234"

    user_data = UserCreate(
        email=f"auth-{uuid.uuid4()}@example.com",
        password=password
    )

    response = create_user(db, user_data)
    user = db.get(User, response.id)

    try:
        yield user
    finally:
        if user is not None:
            db.delete(user)
            db.commit()


def test_create_user(db):
    email = f"create-{uuid.uuid4()}@example.com"

    user_data = UserCreate(
        email=email,
        password="test1234"
    )

    created_user = None

    try:
        response = create_user(db, user_data)

        assert isinstance(response, UserResponse)
        assert response.email == email
        assert response.id is not None
        assert not hasattr(response, "password")
        assert not hasattr(response, "password_hash")

        created_user = db.get(User, response.id)

    finally:
        if created_user is not None:
            db.delete(created_user)
            db.commit()


def test_create_user_rejects_duplicate_email(db):
    email = f"duplicate-{uuid.uuid4()}@example.com"

    first_user = None

    try:
        first_response = create_user(
            db,
            UserCreate(
                email=email,
                password="test1234"
            )
        )

        first_user = db.get(User, first_response.id)

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
        if first_user is not None:
            db.delete(first_user)
            db.commit()


def test_authenticate_user_with_correct_password(db, test_user):
    user_data = UserLogin(
        email=test_user.email,
        password="test1234"
    )

    result = authenticate_user(db, user_data)

    assert isinstance(result, User)
    assert result.id == test_user.id
    assert result.email == test_user.email


def test_authenticate_user_rejects_wrong_password(db, test_user):
    user_data = UserLogin(
        email=test_user.email,
        password="wrongpassword"
    )

    with pytest.raises(
        ValueError,
        match="Incorrect email or password"
    ):
        authenticate_user(db, user_data)


def test_authenticate_user_rejects_unknown_email(db):
    user_data = UserLogin(
        email=f"unknown-{uuid.uuid4()}@example.com",
        password="test1234"
    )

    with pytest.raises(
        ValueError,
        match="Incorrect email or password"
    ):
        authenticate_user(db, user_data)
