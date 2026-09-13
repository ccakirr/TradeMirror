import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Numeric,
    Boolean,
    DateTime,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db import Base


class TradingAccount(Base):
    __tablename__ = "trading_accounts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user = relationship(
        "User",
        back_populates="accounts"
    )

    name = Column(
        String(100),
        nullable=False
    )

    initial_balance = Column(
        Numeric(18, 4),
        nullable=False
    )

    current_balance = Column(
        Numeric(18, 4),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
