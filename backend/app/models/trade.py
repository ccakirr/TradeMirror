import uuid

from sqlalchemy import (
    Column,
    String,
    Numeric,
    ForeignKey,
    Boolean,
    DateTime,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    trading_account = relationship(
        "TradingAccount",
        back_populates="trades"
    )

    instrument = Column(
        String,
        nullable=False
    )

    is_long = Column(
        Boolean,
        nullable=False
    )

    is_closed = Column(
        Boolean,
        nullable=False,
        default=False
    )

    entry_price = Column(
        Numeric(18, 4),
        nullable=False
    )

    exit_price = Column(
        Numeric(18, 4),
    )

    position_size = Column(
        Numeric(18, 4),
        nullable=False
    )

    stop_loss = Column(
        Numeric(18, 4),
    )

    take_profit = Column(
        Numeric(18, 4),
    )

    opened_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    closed_at = Column(
        DateTime(timezone=True),
    )

    pnl = Column(
        Numeric(18, 4),
    )

    notes = Column(
        Text,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
