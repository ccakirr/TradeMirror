from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class TradeReviewCreate(BaseModel):
    plan_adherence: Literal["followed", "partially_followed", "broken", "unknown"]
    setup_followed: bool
    pre_trade_emotion: str | None = Field(default=None, max_length=64)
    post_trade_emotion: str | None = Field(default=None, max_length=64)
    mistake_tags: list[str] = Field(default_factory=list, max_length=12)
    lesson: str | None = Field(default=None, max_length=2000)


class TradeReviewResponse(TradeReviewCreate):
    id: UUID
    trade_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
