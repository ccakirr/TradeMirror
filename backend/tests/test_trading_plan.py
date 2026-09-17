import uuid
from decimal import Decimal

import pytest

from ..app.db import SessionLocal
from ..app.models.trade import Trade
from ..app.models.trading_accounts import TradingAccount
from ..app.models.trading_plan import TradingPlan
from ..app.models.user import User
from ..app.schemas.plan import TradingPlanCreate
from ..app.schemas.trade import TradeCreate
from ..app.services.trade import create_trade
from ..app.services.trading_plan import (
    create_trading_plan,
    get_active_trading_plan,
    list_trading_plans,
)


def plan_data(**overrides):
    fields = {
        "max_risk_per_trade_pct": Decimal("1"),
        "max_daily_loss_pct": Decimal("3"),
        "max_trades_per_day": 5,
        "max_open_positions": 3,
        "require_stop_loss": True,
        "allowed_instruments": ["BTCUSDT"],
        "allowed_setups": ["breakout"],
    }
    fields.update(overrides)
    return TradingPlanCreate(**fields)


def trade_data(**overrides):
    fields = {
        "instrument": "BTCUSDT",
        "is_long": True,
        "entry_price": Decimal("50000"),
        "position_size": Decimal("0.1"),
        "stop_loss": Decimal("49000"),
        "take_profit": Decimal("52000"),
        "notes": None,
    }
    fields.update(overrides)
    return TradeCreate(**fields)


def make_user(db, prefix):
    user = User(email=f"{prefix}-{uuid.uuid4()}@example.com", password_hash="fake_hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_account(db, user):
    account = TradingAccount(
        user_id=user.id,
        name="Plan Account",
        initial_balance=Decimal("10000"),
        current_balance=Decimal("10000"),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def clean(db, *rows):
    for row in rows:
        if row is not None:
            db.delete(row)
    db.commit()
    db.close()


def test_the_first_plan_is_version_one_and_open_ended():
    db = SessionLocal()
    user = account = None

    try:
        user = make_user(db, "plan")
        account = make_account(db, user)

        plan = create_trading_plan(db, user, account.id, plan_data())

        assert plan.version == 1
        assert plan.valid_to is None
        assert plan.max_risk_per_trade_pct == Decimal("1")
        assert plan.allowed_instruments == ["BTCUSDT"]
        assert plan.require_stop_loss is True

    except Exception:
        db.rollback()
        raise

    finally:
        clean(db, account, user)


def test_publishing_a_version_closes_the_one_before_it():
    db = SessionLocal()
    user = account = None

    try:
        user = make_user(db, "plan-version")
        account = make_account(db, user)

        first = create_trading_plan(db, user, account.id, plan_data())
        second = create_trading_plan(
            db, user, account.id, plan_data(max_risk_per_trade_pct=Decimal("0.5"))
        )

        closed = db.get(TradingPlan, first.id)

        assert second.version == 2
        assert second.valid_to is None
        # The replaced version keeps its rules and gains an end date, so the
        # limits in force last month are still recoverable.
        assert closed.valid_to is not None
        assert closed.max_risk_per_trade_pct == Decimal("1")

        active = get_active_trading_plan(db, account.id)
        assert active.id == second.id

        history = list_trading_plans(db, user, account.id)
        assert [item.version for item in history] == [2, 1]

    except Exception:
        db.rollback()
        raise

    finally:
        clean(db, account, user)


def test_a_new_trade_is_stamped_with_the_active_plan():
    db = SessionLocal()
    user = account = None

    try:
        user = make_user(db, "plan-trade")
        account = make_account(db, user)

        before = create_trade(db, user, account.id, trade_data())
        assert before.plan_id is None

        plan = create_trading_plan(db, user, account.id, plan_data())
        after = create_trade(db, user, account.id, trade_data())

        assert after.plan_id == plan.id

        # A version published later does not re-stamp a trade already logged.
        create_trading_plan(db, user, account.id, plan_data(max_daily_loss_pct=Decimal("2")))
        assert db.get(Trade, after.id).plan_id == plan.id

    except Exception:
        db.rollback()
        raise

    finally:
        for trade in db.query(Trade).filter(Trade.account_id == account.id).all():
            db.delete(trade)
        db.commit()
        clean(db, account, user)


def test_another_users_account_has_no_plans_to_read_or_write():
    db = SessionLocal()
    owner = stranger = account = None

    try:
        owner = make_user(db, "plan-owner")
        stranger = make_user(db, "plan-stranger")
        account = make_account(db, owner)

        with pytest.raises(ValueError):
            create_trading_plan(db, stranger, account.id, plan_data())

        with pytest.raises(ValueError):
            list_trading_plans(db, stranger, account.id)

    except Exception:
        db.rollback()
        raise

    finally:
        clean(db, account, owner, stranger)
