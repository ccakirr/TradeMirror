from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Literal
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from .common import plain_decimal


Level = Literal["good", "info", "warn", "bad"]


class RiskReportFinding(BaseModel):
    """One explainable line of the report.

    The wording lives in the client so both languages read naturally; the
    backend ships the rule that fired plus the numbers behind it.
    """

    code: str
    level: Level
    values: dict[str, str] = {}


class RiskReportResponse(BaseModel):
    trade_id: UUID
    generated_at: datetime
    risk_class: Literal["low", "medium", "high"]

    # The model's own read of the account, when an assessment was stored.
    score: Decimal | None = None
    threshold: Decimal | None = None
    model_version: str | None = None
    model_stage: Literal["entry", "exit"] | None = None

    # Rule-based metrics — computed from the trade itself, always explainable.
    risk_amount: Decimal | None = None
    risk_pct: Decimal | None = None
    risk_limit_pct: Decimal
    reward_risk: Decimal | None = None
    notional: Decimal
    exposure_pct: Decimal
    r_multiple: Decimal | None = None
    holding_days: Decimal | None = None

    findings: list[RiskReportFinding]

    model_config = ConfigDict(from_attributes=True)

    @field_serializer(
        "score",
        "threshold",
        "risk_amount",
        "risk_pct",
        "risk_limit_pct",
        "reward_risk",
        "notional",
        "exposure_pct",
        "r_multiple",
        "holding_days",
    )
    def trim(self, value: Decimal | None) -> str | None:
        return plain_decimal(value)
