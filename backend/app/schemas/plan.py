from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .common import plain_decimal


class TradingPlanCreate(BaseModel):
    max_risk_per_trade_pct: Decimal = Field(ge=0)
    max_daily_loss_pct: Decimal = Field(ge=0)
    max_trades_per_day: int | None = Field(default=None, gt=0)
    require_stop_loss: bool = True
    max_open_positions: int | None = Field(default=None, gt=0)
    allowed_instruments: list[str] = Field(default_factory=list)
    allowed_setups: list[str] = Field(default_factory=list)


class TradingPlanResponse(TradingPlanCreate):
    id: UUID
    account_id: UUID
    version: int
    valid_from: datetime
    valid_to: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("max_risk_per_trade_pct", "max_daily_loss_pct")
    def trim_decimal(self, value: Decimal) -> str:
        return plain_decimal(value)
