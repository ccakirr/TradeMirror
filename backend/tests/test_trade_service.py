import uuid
from decimal import Decimal

import pytest

from ..app.db import SessionLocal
from ..app.models.user import User
from ..app.models.trade import Trade
from ..app.models.trading_accounts import TradingAccount
from ..app.schemas.trade import TradeCreate, TradeResponse, TradeClose
from ..app.services.trade import (
    create_trade,
    close_trade,
    get_trade,
    TradeValidationError,
)


def test_create_trade_for_owned_account():
    db = SessionLocal()

    user = None
    account = None
    trade = None

    try:
        user = User(
            email=f"trade-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="Main Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        trade_data = TradeCreate(
            instrument="BTCUSDT",
            is_long=True,
            entry_price=Decimal("50000"),
            position_size=Decimal("0.1"),
            stop_loss=Decimal("49000"),
            take_profit=Decimal("52000"),
            notes="Test trade",
        )

        response = create_trade(
            db=db,
            current_user=user,
            account_id=account.id,
            trade_data=trade_data,
        )

        trade = db.get(Trade, response.id)

        assert isinstance(response, TradeResponse)
        assert response.id is not None
        assert response.account_id == account.id
        assert response.instrument == "BTCUSDT"
        assert response.is_long is True
        assert response.is_closed is False
        assert response.entry_price == Decimal("50000")
        assert response.position_size == Decimal("0.1")
        assert response.exit_price is None
        assert response.closed_at is None
        assert response.pnl is None

    except Exception:
        db.rollback()
        raise

    finally:
        if trade is not None:
            db.delete(trade)

        if account is not None:
            db.delete(account)

        if user is not None:
            db.delete(user)

        db.commit()
        db.close()


def test_user_cannot_create_trade_for_other_users_account():
    db = SessionLocal()

    owner = None
    other_user = None
    account = None

    try:
        owner = User(
            email=f"owner-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )

        other_user = User(
            email=f"other-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )

        db.add_all([owner, other_user])
        db.commit()
        db.refresh(owner)
        db.refresh(other_user)

        account = TradingAccount(
            user_id=owner.id,
            name="Owner Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        trade_data = TradeCreate(
            instrument="EURUSD",
            is_long=False,
            entry_price=Decimal("1.1000"),
            position_size=Decimal("1000"),
        )

        with pytest.raises(
            ValueError,
            match="Trading account not found",
        ):
            create_trade(
                db=db,
                current_user=other_user,
                account_id=account.id,
                trade_data=trade_data,
            )

    except Exception:
        db.rollback()
        raise

    finally:
        if account is not None:
            db.delete(account)

        if other_user is not None:
            db.delete(other_user)

        if owner is not None:
            db.delete(owner)

        db.commit()
        db.close()


def test_close_long_trade_updates_pnl_and_account_balance():
    db = SessionLocal()
    user = account = trade = None

    try:
        user = User(
            email=f"close-long-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="Long Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        trade = Trade(
            account_id=account.id,
            instrument="BTCUSDT",
            is_long=True,
            is_closed=False,
            entry_price=Decimal("100"),
            position_size=Decimal("2"),
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        response = close_trade(
            db=db,
            current_user=user,
            account_id=account.id,
            trade_id=trade.id,
            trade_data=TradeClose(exit_price=Decimal("110")),
        )
        db.refresh(account)

        assert response.is_closed is True
        assert response.exit_price == Decimal("110")
        assert response.pnl == Decimal("20.0000")
        assert account.current_balance == Decimal("1020.0000")
        assert response.closed_at is not None

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if user is not None:
            db.delete(user)
        db.commit()
        db.close()


def test_close_short_trade_calculates_pnl_correctly():
    db = SessionLocal()
    user = account = trade = None

    try:
        user = User(
            email=f"close-short-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="Short Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        trade = Trade(
            account_id=account.id,
            instrument="EURUSD",
            is_long=False,
            is_closed=False,
            entry_price=Decimal("100"),
            position_size=Decimal("2"),
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        response = close_trade(
            db=db,
            current_user=user,
            account_id=account.id,
            trade_id=trade.id,
            trade_data=TradeClose(exit_price=Decimal("90")),
        )
        db.refresh(account)

        assert response.is_closed is True
        assert response.pnl == Decimal("20.0000")
        assert account.current_balance == Decimal("1020.0000")

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if user is not None:
            db.delete(user)
        db.commit()
        db.close()


def test_closed_trade_cannot_be_closed_twice():
    db = SessionLocal()
    user = account = trade = None

    try:
        user = User(
            email=f"close-twice-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="Closed Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        trade = Trade(
            account_id=account.id,
            instrument="ETHUSDT",
            is_long=True,
            is_closed=True,
            entry_price=Decimal("100"),
            exit_price=Decimal("110"),
            position_size=Decimal("1"),
            pnl=Decimal("10"),
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        with pytest.raises(ValueError, match="Trade is already closed"):
            close_trade(
                db=db,
                current_user=user,
                account_id=account.id,
                trade_id=trade.id,
                trade_data=TradeClose(exit_price=Decimal("120")),
            )

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if user is not None:
            db.delete(user)
        db.commit()
        db.close()


def test_get_trade_returns_full_detail():
    db = SessionLocal()
    user = account = trade = None

    try:
        user = User(
            email=f"detail-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="Detail Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1120"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        trade = Trade(
            account_id=account.id,
            instrument="BTCUSDT",
            is_long=True,
            is_closed=True,
            entry_price=Decimal("50000"),
            exit_price=Decimal("51200"),
            position_size=Decimal("0.1"),
            stop_loss=Decimal("49000"),
            take_profit=Decimal("52000"),
            pnl=Decimal("120"),
            notes="Breakout retest",
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        response = get_trade(
            db=db,
            current_user=user,
            account_id=account.id,
            trade_id=trade.id,
        )

        assert isinstance(response, TradeResponse)
        assert response.id == trade.id
        assert response.account_id == account.id
        assert response.instrument == "BTCUSDT"
        assert response.entry_price == Decimal("50000")
        assert response.exit_price == Decimal("51200")
        assert response.stop_loss == Decimal("49000")
        assert response.take_profit == Decimal("52000")
        assert response.pnl == Decimal("120")
        assert response.notes == "Breakout retest"

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if user is not None:
            db.delete(user)
        db.commit()
        db.close()


def test_get_trade_rejects_other_users_account():
    db = SessionLocal()
    owner = other_user = account = trade = None

    try:
        owner = User(
            email=f"detail-owner-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        other_user = User(
            email=f"detail-other-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add_all([owner, other_user])
        db.commit()
        db.refresh(owner)
        db.refresh(other_user)

        account = TradingAccount(
            user_id=owner.id,
            name="Owner Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        trade = Trade(
            account_id=account.id,
            instrument="EURUSD",
            is_long=False,
            is_closed=False,
            entry_price=Decimal("1.1000"),
            position_size=Decimal("1000"),
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        with pytest.raises(ValueError, match="Trading account not found"):
            get_trade(
                db=db,
                current_user=other_user,
                account_id=account.id,
                trade_id=trade.id,
            )

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if owner is not None:
            db.delete(owner)
        if other_user is not None:
            db.delete(other_user)
        db.commit()
        db.close()


def test_get_trade_rejects_trade_from_another_account():
    db = SessionLocal()
    user = account = other_account = trade = None

    try:
        user = User(
            email=f"detail-cross-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="First Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        other_account = TradingAccount(
            user_id=user.id,
            name="Second Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add_all([account, other_account])
        db.commit()
        db.refresh(account)
        db.refresh(other_account)

        trade = Trade(
            account_id=account.id,
            instrument="XAUUSD",
            is_long=True,
            is_closed=False,
            entry_price=Decimal("2400"),
            position_size=Decimal("1"),
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        # Same owner, wrong account: the trade must not leak across journals.
        with pytest.raises(ValueError, match="Trade not found"):
            get_trade(
                db=db,
                current_user=user,
                account_id=other_account.id,
                trade_id=trade.id,
            )

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if other_account is not None:
            db.delete(other_account)
        if user is not None:
            db.delete(user)
        db.commit()
        db.close()


def test_close_trade_rejects_exit_price_off_the_instrument_step():
    db = SessionLocal()
    user = account = trade = None

    try:
        user = User(
            email=f"close-step-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="Step Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        trade = Trade(
            account_id=account.id,
            instrument="BTCUSDT",
            is_long=True,
            is_closed=False,
            entry_price=Decimal("50000"),
            position_size=Decimal("0.1"),
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        with pytest.raises(TradeValidationError, match="multiple of 0.01"):
            close_trade(
                db=db,
                current_user=user,
                account_id=account.id,
                trade_id=trade.id,
                trade_data=TradeClose(exit_price=Decimal("51000.123")),
            )

        db.refresh(trade)

        assert trade.is_closed is False
        assert account.current_balance == Decimal("1000")

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if user is not None:
            db.delete(user)
        db.commit()
        db.close()


def test_close_trade_allows_a_symbol_missing_from_the_catalog():
    db = SessionLocal()
    user = account = trade = None

    try:
        user = User(
            email=f"close-legacy-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="Legacy Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        # Journaled before the catalog existed: it must still be closable.
        trade = Trade(
            account_id=account.id,
            instrument="RETIRED-PAIR",
            is_long=True,
            is_closed=False,
            entry_price=Decimal("100"),
            position_size=Decimal("1"),
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        response = close_trade(
            db=db,
            current_user=user,
            account_id=account.id,
            trade_id=trade.id,
            trade_data=TradeClose(exit_price=Decimal("110.1234")),
        )

        assert response.is_closed is True
        assert response.pnl == Decimal("10.1234")

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if user is not None:
            db.delete(user)
        db.commit()
        db.close()


def test_eight_decimal_prices_round_trip_through_postgres():
    """Numeric(18, 4) silently flattened these to 0.0000; Numeric(28, 10) holds them."""
    db = SessionLocal()
    user = account = trade = None

    try:
        user = User(
            email=f"precision-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = TradingAccount(
            user_id=user.id,
            name="Precision Account",
            initial_balance=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        response = create_trade(
            db=db,
            current_user=user,
            account_id=account.id,
            trade_data=TradeCreate(
                instrument="SHIBUSDT",
                is_long=True,
                entry_price=Decimal("0.00001234"),
                position_size=Decimal("1000000"),
                stop_loss=Decimal("0.00001180"),
            ),
        )
        trade = db.get(Trade, response.id)

        assert trade.entry_price == Decimal("0.00001234")
        assert trade.stop_loss == Decimal("0.00001180")

        closed = close_trade(
            db=db,
            current_user=user,
            account_id=account.id,
            trade_id=trade.id,
            trade_data=TradeClose(exit_price=Decimal("0.00001400")),
        )

        # (0.00001400 - 0.00001234) * 1_000_000
        assert closed.exit_price == Decimal("0.00001400")
        assert closed.pnl == Decimal("1.66")

        db.refresh(account)
        assert account.current_balance == Decimal("1001.66")

    finally:
        if trade is not None:
            db.delete(trade)
        if account is not None:
            db.delete(account)
        if user is not None:
            db.delete(user)
        db.commit()
        db.close()
