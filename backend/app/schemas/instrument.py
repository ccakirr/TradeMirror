from decimal import Decimal

from .common import plain_decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class InstrumentResponse(BaseModel):
    symbol: str
    name: str
    category: str
    venue: str
    price_step: Decimal
    size_step: Decimal

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("price_step", "size_step")
    def trim(self, value: Decimal) -> str:
        return plain_decimal(value)
