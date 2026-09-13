from pydantic import BaseModel, Field, EmailStr, SecretStr, ConfigDict
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=100)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    timezone: str
    currency: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
