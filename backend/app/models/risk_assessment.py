import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    trade_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trades.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    stage = Column(String(16), nullable=False)
    score = Column(Numeric(18, 10), nullable=False)
    risk_class = Column(String(16), nullable=False)
    threshold = Column(Numeric(18, 10), nullable=False)
    model_version = Column(String(64), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    trade = relationship("Trade", back_populates="risk_assessments")
