from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.instruments import get_instrument, is_on_step
from ..models.user import User
from ..models.trading_accounts import TradingAccount
from ..models.trade import Trade
from ..schemas.trade import TradeCreate, TradeResponse, TradeClose
from .risk_assessment import create_automatic_risk_assessment


class TradeValidationError(ValueError):
    """A well-formed request whose numbers do not fit the instrument."""


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

    create_automatic_risk_assessment(db, account, trade, "entry")

    return TradeResponse.model_validate(trade)


def close_trade(
    db: Session,
    current_user: User,
    account_id: UUID,
    trade_id: UUID,
    trade_data: TradeClose,
) -> TradeResponse:
    account = db.get(TradingAccount, account_id)
    trade = db.get(Trade, trade_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    if trade is None or trade.account_id != account.id:
        raise ValueError("Trade not found")

    if trade.is_closed:
        raise ValueError("Trade is already closed")

    # Trades journaled before an instrument left the catalog keep their old
    # symbol; those can still be closed, just without the step check.
    instrument = get_instrument(trade.instrument)

    if instrument is not None and not is_on_step(
        trade_data.exit_price, instrument.price_step
    ):
        raise TradeValidationError(
            f"exit_price must be a multiple of {instrument.price_step}"
        )

    trade.exit_price = trade_data.exit_price
    trade.is_closed = True
    trade.closed_at = datetime.now(timezone.utc)
    price_difference = (
        trade.exit_price - trade.entry_price if trade.is_long
        else trade.entry_price - trade.exit_price
    )
    trade.pnl = price_difference * trade.position_size
    account.current_balance = account.current_balance + trade.pnl

    try:
        db.commit()
        db.refresh(trade)
    except Exception:
        db.rollback()
        raise

    create_automatic_risk_assessment(db, account, trade, "exit")

    return TradeResponse.model_validate(trade)


def get_trade(
    db: Session,
    current_user: User,
    account_id: UUID,
    trade_id: UUID,
) -> TradeResponse:
    account = db.get(TradingAccount, account_id)
    trade = db.get(Trade, trade_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    if trade is None or trade.account_id != account.id:
        raise ValueError("Trade not found")

    return TradeResponse.model_validate(trade)


def list_trades(
    db: Session,
    current_user: User,
    account_id: UUID,
) -> list[TradeResponse]:
    account = db.get(TradingAccount, account_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    trades = db.scalars(
        select(Trade)
        .where(Trade.account_id == account.id)
        .order_by(Trade.opened_at.desc())
    ).all()

    return [TradeResponse.model_validate(trade) for trade in trades]
