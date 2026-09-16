from pydantic import BaseModel, ConfigDict, Field, field_serializer
from typing import Literal
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from .common import plain_decimal


class PredictorResponse(BaseModel):
    score: float
    risk_class: Literal[
        "high",
        "medium",
        "low"
    ]
    threshold: float
    model_version: str


class RiskAssessmentResponse(BaseModel):
    id: UUID
    trade_id: UUID
    stage: Literal["entry", "exit"]
    score: Decimal
    risk_class: Literal["high", "medium", "low"]
    threshold: Decimal
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("score", "threshold")
    def trim_decimal(self, value: Decimal) -> str:
        return plain_decimal(value)


class PredictorRequest(BaseModel):
    starting_capital: float = Field(gt=0)
    account_age_months: int = Field(ge=0)
    instrument: Literal[
        'forex',
        'futures',
        'stocks',
        'crypto',
        'options',
        'etf'
    ]
    risk_per_trade_pct: float = Field(ge=0)
    trades_per_month: float = Field(ge=0)
    uses_stop_loss: Literal[1, 0]
    avg_win_hold_days: float = Field(ge=0)
    avg_loss_hold_days: float = Field(ge=0)
    diversification: float = Field(ge=0)
    follows_plan: float = Field(ge=0, le=10)
    position_sizing_discipline: float = Field(ge=0, le=10)


class RiskAssessmentCreate(PredictorRequest):
    stage: Literal["entry", "exit"]
