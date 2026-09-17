from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.trading_accounts import TradingAccount
from ..models.trading_plan import TradingPlan
from ..models.user import User
from ..schemas.plan import TradingPlanCreate, TradingPlanResponse


def create_trading_plan(
    db: Session,
    current_user: User,
    account_id: UUID,
    plan_data: TradingPlanCreate,
) -> TradingPlanResponse:
    account = db.get(TradingAccount, account_id)
    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    active = db.scalar(
        select(TradingPlan)
        .where(TradingPlan.account_id == account.id)
        .where(TradingPlan.valid_to.is_(None))
        .order_by(TradingPlan.version.desc())
    )
    now = datetime.now(timezone.utc)
    version = 1
    if active is not None:
        active.valid_to = now
        version = active.version + 1

    plan = TradingPlan(
        account_id=account.id,
        version=version,
        valid_from=now,
        **plan_data.model_dump(),
    )

    try:
        db.add(plan)
        db.commit()
        db.refresh(plan)
    except Exception:
        db.rollback()
        raise

    return TradingPlanResponse.model_validate(plan)


def list_trading_plans(
    db: Session,
    current_user: User,
    account_id: UUID,
) -> list[TradingPlanResponse]:
    account = db.get(TradingAccount, account_id)
    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    plans = db.scalars(
        select(TradingPlan)
        .where(TradingPlan.account_id == account.id)
        .order_by(TradingPlan.version.desc())
    ).all()
    return [TradingPlanResponse.model_validate(plan) for plan in plans]


def get_active_trading_plan(
    db: Session,
    account_id: UUID,
) -> TradingPlan | None:
    return db.scalar(
        select(TradingPlan)
        .where(TradingPlan.account_id == account_id)
        .where(TradingPlan.valid_to.is_(None))
        .order_by(TradingPlan.version.desc())
    )
