from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.trade import Trade
from ..models.trade_review import TradeReview
from ..models.trading_accounts import TradingAccount
from ..models.user import User
from ..schemas.review import TradeReviewCreate, TradeReviewResponse


def save_trade_review(
    db: Session,
    current_user: User,
    account_id: UUID,
    trade_id: UUID,
    review_data: TradeReviewCreate,
) -> TradeReviewResponse:
    account = db.get(TradingAccount, account_id)
    trade = db.get(Trade, trade_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")
    if trade is None or trade.account_id != account.id:
        raise ValueError("Trade not found")
    if not trade.is_closed:
        raise ValueError("Trade must be closed before review")

    review = db.scalar(select(TradeReview).where(TradeReview.trade_id == trade.id))
    if review is None:
        review = TradeReview(trade_id=trade.id)
        db.add(review)

    for field, value in review_data.model_dump().items():
        setattr(review, field, value)

    try:
        db.commit()
        db.refresh(review)
    except Exception:
        db.rollback()
        raise

    return TradeReviewResponse.model_validate(review)


def get_trade_review(
    db: Session,
    current_user: User,
    account_id: UUID,
    trade_id: UUID,
) -> TradeReviewResponse | None:
    account = db.get(TradingAccount, account_id)
    trade = db.get(Trade, trade_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")
    if trade is None or trade.account_id != account.id:
        raise ValueError("Trade not found")

    review = db.scalar(select(TradeReview).where(TradeReview.trade_id == trade.id))
    return None if review is None else TradeReviewResponse.model_validate(review)
