from pydantic import BaseModel, Field
from typing import Literal


class PredictorResponse(BaseModel):
    score: float
    risk_class: Literal[
        "high",
        "medium",
        "low"
    ]
    threshold: float
    model_version: str


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
