from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from uuid import UUID
from datetime import datetime


class TradeCreate(BaseModel):
    instrument: str = Field(min_length=1, max_length=32)
    is_long: bool
    entry_price: Decimal = Field(gt=0)
    position_size: Decimal = Field(gt=0)
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    notes: str | None = None


class TradeResponse(BaseModel):
    id: UUID
    account_id: UUID
    instrument: str
    is_long: bool
    is_closed: bool
    entry_price: Decimal
    exit_price: Decimal | None
    position_size: Decimal
    stop_loss: Decimal | None
    take_profit: Decimal | None
    opened_at: datetime
    closed_at: datetime | None
    pnl: Decimal | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
