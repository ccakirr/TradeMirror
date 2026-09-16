from sqlalchemy import select
from sqlalchemy.orm import Session

from uuid import UUID

from ..schemas.account import (
    TradingAccountCreate,
    TradingAccountResponse,
    TradingAccountRiskProfileCreate,
    TradingAccountRiskProfileResponse,
)
from ..models.user import User
from ..models.trading_accounts import TradingAccount
from ..models.risk_profile import TradingAccountRiskProfile


def create_trading_account(
        db: Session,
        current_user: User,
        account_data: TradingAccountCreate
) -> TradingAccountResponse:
    user_id = current_user.id
    balance = account_data.initial_balance

    trade_account = TradingAccount(
        user_id=user_id,
        initial_balance=balance,
        current_balance=balance,
        name=account_data.name,
    )

    try:
        db.add(trade_account)
        db.commit()
        db.refresh(trade_account)
    except Exception:
        db.rollback()
        raise

    return TradingAccountResponse.model_validate(trade_account)


def list_trading_accounts(
    db: Session,
    current_user: User,
) -> list[TradingAccountResponse]:
    accounts = db.scalars(
        select(TradingAccount)
        .where(TradingAccount.user_id == current_user.id)
        .where(TradingAccount.is_active.is_(True))
        .order_by(TradingAccount.created_at.desc())
    ).all()

    return [
        TradingAccountResponse.model_validate(account) for account in accounts
    ]


def save_risk_profile(
    db: Session,
    current_user: User,
    account_id: UUID,
    profile_data: TradingAccountRiskProfileCreate,
) -> TradingAccountRiskProfileResponse:
    account = db.get(TradingAccount, account_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    profile = db.scalar(
        select(TradingAccountRiskProfile).where(
            TradingAccountRiskProfile.account_id == account.id
        )
    )

    if profile is None:
        profile = TradingAccountRiskProfile(account_id=account.id)
        db.add(profile)

    for field, value in profile_data.model_dump().items():
        setattr(profile, field, value)

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return TradingAccountRiskProfileResponse.model_validate(profile)


def get_risk_profile(
    db: Session,
    current_user: User,
    account_id: UUID,
) -> TradingAccountRiskProfileResponse:
    account = db.get(TradingAccount, account_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    profile = db.scalar(
        select(TradingAccountRiskProfile).where(
            TradingAccountRiskProfile.account_id == account.id
        )
    )

    if profile is None:
        raise ValueError("Risk profile not found")

    return TradingAccountRiskProfileResponse.model_validate(profile)
