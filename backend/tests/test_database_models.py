from ..app.db import SessionLocal
from ..app.models import User, TradingAccount

import uuid


def test_create_trading_account_for_user():
    db = SessionLocal()

    user = None
    trading_account = None

    try:
        user = User(
            email=f"test-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        trading_account = TradingAccount(
            user=user,
            name="Test Account",
            initial_balance=1000,
            current_balance=1000,
        )

        db.add(trading_account)
        db.commit()
        db.refresh(trading_account)

        saved_account = db.get(
            TradingAccount,
            trading_account.id
        )

        assert saved_account is not None
        assert saved_account.name == "Test Account"
        assert saved_account.user_id == user.id
        assert trading_account.user == user
        assert trading_account in user.accounts
        assert trading_account.user_id == user.id

    except Exception:
        db.rollback()
        raise

    finally:
        if trading_account is not None:
            db.delete(trading_account)

        if user is not None:
            db.delete(user)

        db.commit()
        db.close()
