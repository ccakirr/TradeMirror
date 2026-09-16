from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from ..core.instruments import get_instrument, is_on_step
from .common import plain_decimal


class TradeCreate(BaseModel):
    instrument: str = Field(min_length=1, max_length=32)
    is_long: bool
    entry_price: Decimal = Field(gt=0)
    position_size: Decimal = Field(gt=0)
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    notes: str | None = None

    @field_validator("instrument")
    @classmethod
    def known_instrument(cls, value: str) -> str:
        symbol = value.strip().upper()

        if get_instrument(symbol) is None:
            raise ValueError("Unknown instrument")

        return symbol

    @model_validator(mode="after")
    def prices_follow_instrument_steps(self) -> "TradeCreate":
        instrument = get_instrument(self.instrument)

        prices = {
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
        }

        for name, value in prices.items():
            if value is not None and not is_on_step(value, instrument.price_step):
                raise ValueError(
                    f"{name} must be a multiple of {instrument.price_step}"
                )

        if not is_on_step(self.position_size, instrument.size_step):
            raise ValueError(
                f"position_size must be a multiple of {instrument.size_step}"
            )

        return self


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

    @field_serializer(
        "entry_price",
        "exit_price",
        "position_size",
        "stop_loss",
        "take_profit",
        "pnl",
    )
    def trim(self, value: Decimal | None) -> str | None:
        return plain_decimal(value)


class TradeClose(BaseModel):
    exit_price: Decimal = Field(gt=0)
