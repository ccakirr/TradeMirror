import uuid

from ..app.db import SessionLocal
from ..app.models.user import User
from ..app.models.trading_accounts import TradingAccount
from ..app.schemas.account import (
    TradingAccountCreate,
    TradingAccountResponse,
)
from ..app.services.trading_account import create_trading_account


def test_create_trading_account():
    db = SessionLocal()

    user = None
    trading_account = None

    try:
        user = User(
            email=f"account-{uuid.uuid4()}@example.com",
            password_hash="fake_hash",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        account_data = TradingAccountCreate(
            name="Main Account",
            initial_balance=1000,
        )

        response = create_trading_account(
            db=db,
            current_user=user,
            account_data=account_data,
        )

        trading_account = db.get(TradingAccount, response.id)

        assert isinstance(response, TradingAccountResponse)
        assert response.id is not None
        assert response.user_id == user.id
        assert response.name == "Main Account"
        assert response.initial_balance == 1000
        assert response.current_balance == 1000
        assert response.is_active is True

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
