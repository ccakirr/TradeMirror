from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse, TokenResponse, UserLogin
from ..services.user import create_user, authenticate_user
from ..core.security import create_access_token
from ..db import get_db


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    responses={
        409: {
            "description": "Email already exists"
        }
    }
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    try:
        response = create_user(db, user_data)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {
            "description": "Incorrect email or password"
        }
    }
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
) -> TokenResponse:
    try:
        user = authenticate_user(db, user_data)
        token = create_access_token({
            "sub": str(user.id)
        })

        return TokenResponse(
            access_token=token,
            token_type="bearer"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    return UserResponse.model_validate(current_user)
