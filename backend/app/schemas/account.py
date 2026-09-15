from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class TradingAccountCreate(BaseModel):
    name: str = Field(min_length=3, max_length=64)
    initial_balance: Decimal = Field(gt=0)


class TradingAccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    initial_balance: Decimal
    current_balance: Decimal
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
