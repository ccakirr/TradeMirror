from uuid import UUID
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.trading_accounts import TradingAccount
from ..models.trade import Trade
from ..schemas.trade import TradeCreate, TradeResponse


def create_trade(
    db: Session,
    current_user: User,
    account_id: UUID,
    trade_data: TradeCreate,
) -> TradeResponse:
    account = db.get(TradingAccount, account_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    trade = Trade(
        account_id=account.id,
        instrument=trade_data.instrument,
        is_long=trade_data.is_long,
        is_closed=False,
        entry_price=trade_data.entry_price,
        position_size=trade_data.position_size,
        stop_loss=trade_data.stop_loss,
        take_profit=trade_data.take_profit,
        notes=trade_data.notes,
    )

    try:
        db.add(trade)
        db.commit()
        db.refresh(trade)
    except Exception:
        db.rollback()
        raise

    return TradeResponse.model_validate(trade)