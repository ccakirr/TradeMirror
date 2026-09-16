from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.risk_assessment import RiskAssessment
from ..models.trade import Trade
from ..models.trading_accounts import TradingAccount
from ..models.risk_profile import TradingAccountRiskProfile
from ..models.user import User
from ..schemas.predictor import (
    PredictorRequest,
    RiskAssessmentCreate,
    RiskAssessmentResponse,
)
from .predictor import predict


def create_risk_assessment(
    db: Session,
    current_user: User,
    account_id: UUID,
    trade_id: UUID,
    assessment_data: RiskAssessmentCreate,
) -> RiskAssessmentResponse:
    account = db.get(TradingAccount, account_id)
    trade = db.get(Trade, trade_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    if trade is None or trade.account_id != account.id:
        raise ValueError("Trade not found")

    prediction_input = PredictorRequest.model_validate(
        assessment_data.model_dump(exclude={"stage"})
    )
    prediction = predict(prediction_input)
    assessment = RiskAssessment(
        trade_id=trade.id,
        stage=assessment_data.stage,
        score=prediction.score,
        risk_class=prediction.risk_class,
        threshold=prediction.threshold,
        model_version=prediction.model_version,
    )

    try:
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
    except Exception:
        db.rollback()
        raise

    return RiskAssessmentResponse.model_validate(assessment)


def list_risk_assessments(
    db: Session,
    current_user: User,
    account_id: UUID,
    trade_id: UUID,
) -> list[RiskAssessmentResponse]:
    account = db.get(TradingAccount, account_id)
    trade = db.get(Trade, trade_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    if trade is None or trade.account_id != account.id:
        raise ValueError("Trade not found")

    assessments = db.scalars(
        select(RiskAssessment)
        .where(RiskAssessment.trade_id == trade.id)
        .order_by(RiskAssessment.created_at.asc())
    ).all()

    return [
        RiskAssessmentResponse.model_validate(item)
        for item in assessments
    ]


def create_automatic_risk_assessment(
    db: Session,
    account: TradingAccount,
    trade: Trade,
    stage: str,
) -> RiskAssessmentResponse | None:
    profile = db.scalar(
        select(TradingAccountRiskProfile).where(
            TradingAccountRiskProfile.account_id == account.id
        )
    )

    # Existing accounts may not have a profile yet. The trade remains valid;
    # automatic assessment starts after the user saves one.
    if profile is None:
        return None

    created_at = account.created_at
    if created_at is None:
        account_age_months = 0
    else:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        account_age_months = max(
            0,
            int((datetime.now(timezone.utc) - created_at).days / 30),
        )

    assessment_data = PredictorRequest(
        starting_capital=float(account.initial_balance),
        account_age_months=account_age_months,
        instrument=profile.instrument,
        risk_per_trade_pct=float(profile.risk_per_trade_pct),
        trades_per_month=float(profile.trades_per_month),
        uses_stop_loss=1 if trade.stop_loss is not None else 0,
        avg_win_hold_days=float(profile.avg_win_hold_days),
        avg_loss_hold_days=float(profile.avg_loss_hold_days),
        diversification=float(profile.diversification),
        follows_plan=float(profile.follows_plan),
        position_sizing_discipline=float(profile.position_sizing_discipline),
    )

    prediction = predict(assessment_data)
    assessment = RiskAssessment(
        trade_id=trade.id,
        stage=stage,
        score=prediction.score,
        risk_class=prediction.risk_class,
        threshold=prediction.threshold,
        model_version=prediction.model_version,
    )

    try:
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
    except Exception:
        db.rollback()
        raise

    return RiskAssessmentResponse.model_validate(assessment)
