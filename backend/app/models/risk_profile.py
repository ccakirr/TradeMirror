import uuid

from sqlalchemy import Column, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db import Base


class TradingAccountRiskProfile(Base):
    __tablename__ = "trading_account_risk_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    instrument = Column(String(16), nullable=False)
    risk_per_trade_pct = Column(Numeric(18, 6), nullable=False)
    trades_per_month = Column(Numeric(18, 6), nullable=False)
    avg_win_hold_days = Column(Numeric(18, 6), nullable=False)
    avg_loss_hold_days = Column(Numeric(18, 6), nullable=False)
    diversification = Column(Numeric(18, 6), nullable=False)
    follows_plan = Column(Numeric(18, 6), nullable=False)
    position_sizing_discipline = Column(Numeric(18, 6), nullable=False)

    account = relationship("TradingAccount", back_populates="risk_profile")
