from sqlalchemy.orm import Session

from ..schemas.account import TradingAccountCreate, TradingAccountResponse
from ..models.user import User
from ..models.trading_accounts import TradingAccount


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
