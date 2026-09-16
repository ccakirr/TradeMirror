from pydantic import BaseModel, ConfigDict, Field, field_serializer
from typing import Literal
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from .common import plain_decimal


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

    @field_serializer("initial_balance", "current_balance")
    def trim(self, value: Decimal) -> str:
        return plain_decimal(value)


class TradingAccountRiskProfileCreate(BaseModel):
    instrument: Literal[
        "forex", "futures", "stocks", "crypto", "options", "etf"
    ]
    risk_per_trade_pct: Decimal = Field(ge=0)
    trades_per_month: Decimal = Field(ge=0)
    avg_win_hold_days: Decimal = Field(ge=0)
    avg_loss_hold_days: Decimal = Field(ge=0)
    diversification: Decimal = Field(ge=0)
    follows_plan: Decimal = Field(ge=0, le=10)
    position_sizing_discipline: Decimal = Field(ge=0, le=10)


class TradingAccountRiskProfileResponse(TradingAccountRiskProfileCreate):
    id: UUID
    account_id: UUID

    model_config = ConfigDict(from_attributes=True)
