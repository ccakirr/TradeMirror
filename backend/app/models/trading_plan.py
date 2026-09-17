import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db import Base


class TradingPlan(Base):
    __tablename__ = "trading_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("trading_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    max_risk_per_trade_pct = Column(Numeric(18, 6), nullable=False)
    max_daily_loss_pct = Column(Numeric(18, 6), nullable=False)
    max_trades_per_day = Column(Integer)
    require_stop_loss = Column(Boolean, nullable=False, default=True)
    max_open_positions = Column(Integer)
    allowed_instruments = Column(JSON, nullable=False, default=list)
    allowed_setups = Column(JSON, nullable=False, default=list)
    valid_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valid_to = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    account = relationship("TradingAccount", back_populates="trading_plans")
    trades = relationship("Trade", back_populates="trading_plan")
