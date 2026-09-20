import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db import Base


class TradeReview(Base):
    __tablename__ = "trade_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trades.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    plan_adherence = Column(String(32), nullable=False)
    setup_followed = Column(Boolean, nullable=False)
    pre_trade_emotion = Column(String(64))
    post_trade_emotion = Column(String(64))
    mistake_tags = Column(JSON, nullable=False, default=list)
    lesson = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    trade = relationship("Trade", back_populates="review")
