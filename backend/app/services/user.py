from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schemas.user import UserCreate, UserResponse, UserLogin
from ..models.user import User
from ..core.security import hash_password, verify_password


def create_user(db: Session, user_data: UserCreate) -> UserResponse:
    email = user_data.email.lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is not None:
        raise ValueError("User already exists")

    user = User(
        email=email,
        password_hash=hash_password(
            user_data.password.get_secret_value()
            ),
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return UserResponse.model_validate(user)


def authenticate_user(db: Session, user_data: UserLogin) -> User:
    email = user_data.email.lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is None:
        raise ValueError("Incorrect email or password")

    is_valid_password = verify_password(
        user_data.password.get_secret_value(),
        existing_user.password_hash
    )

    if not is_valid_password:
        raise ValueError("Incorrect email or password")

    return existing_user
