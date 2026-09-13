from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..schemas.user import UserCreate, UserResponse
from ..services.user import create_user
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
