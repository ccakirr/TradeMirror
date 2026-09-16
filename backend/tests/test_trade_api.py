import uuid
from uuid import UUID

from fastapi.testclient import TestClient

from ..app.main import app
from ..app.db import SessionLocal
from ..app.models.user import User
from ..app.models.trade import Trade
from ..app.models.trading_accounts import TradingAccount


client = TestClient(app)


def test_create_trade_api():
    email = f"trade-api-{uuid.uuid4()}@example.com"
    password = "test1234"

    db = SessionLocal()
    user = None
    account = None
    trade = None

    try:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

        assert register_response.status_code == 201

        user_id = UUID(register_response.json()["id"])
        user = db.get(User, user_id)

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}"
        }

        account_response = client.post(
            "/api/v1/accounts/",
            headers=headers,
            json={
                "name": "API Test Account",
                "initial_balance": 1000,
            },
        )

        assert account_response.status_code == 200

        account_id = UUID(account_response.json()["id"])
        account = db.get(TradingAccount, account_id)

        trade_response = client.post(
            f"/api/v1/accounts/{account_id}/trades",
            headers=headers,
            json={
                "instrument": "BTCUSDT",
                "is_long": True,
                "entry_price": 50000,
                "position_size": 0.1,
                "stop_loss": 49000,
                "take_profit": 52000,
                "notes": "API test trade",
            },
        )

        assert trade_response.status_code == 201

        response_data = trade_response.json()
        trade = db.get(Trade, UUID(response_data["id"]))

        assert response_data["account_id"] == str(account_id)
        assert response_data["instrument"] == "BTCUSDT"
        assert response_data["is_long"] is True
        assert response_data["is_closed"] is False
        assert response_data["exit_price"] is None
        assert response_data["closed_at"] is None
        assert response_data["pnl"] is None

    finally:
        if trade is not None:
            db.delete(trade)

        if account is not None:
            db.delete(account)

        if user is not None:
            db.delete(user)

        db.commit()
        db.close()


def test_create_trade_without_token_returns_401():
    fake_account_id = uuid.uuid4()

    response = client.post(
        f"/api/v1/accounts/{fake_account_id}/trades",
        json={
            "instrument": "EURUSD",
            "is_long": False,
            "entry_price": 1.1000,
            "position_size": 1000,
        },
    )

    assert response.status_code == 401


def test_get_trade_detail_api():
    email = f"trade-detail-{uuid.uuid4()}@example.com"
    password = "test1234"

    db = SessionLocal()
    user = None
    account = None
    trade = None

    try:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

        assert register_response.status_code == 201

        user_id = UUID(register_response.json()["id"])
        user = db.get(User, user_id)

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}"
        }

        account_response = client.post(
            "/api/v1/accounts/",
            headers=headers,
            json={
                "name": "Detail API Account",
                "initial_balance": 1000,
            },
        )

        assert account_response.status_code == 200

        account_id = UUID(account_response.json()["id"])
        account = db.get(TradingAccount, account_id)

        create_response = client.post(
            f"/api/v1/accounts/{account_id}/trades",
            headers=headers,
            json={
                "instrument": "BTCUSDT",
                "is_long": True,
                "entry_price": 50000,
                "position_size": 0.1,
                "stop_loss": 49000,
                "take_profit": 52000,
                "notes": "Detail test trade",
            },
        )

        assert create_response.status_code == 201

        trade_id = UUID(create_response.json()["id"])
        trade = db.get(Trade, trade_id)

        detail_response = client.get(
            f"/api/v1/accounts/{account_id}/trades/{trade_id}",
            headers=headers,
        )

        assert detail_response.status_code == 200

        detail = detail_response.json()

        assert detail["id"] == str(trade_id)
        assert detail["account_id"] == str(account_id)
        assert detail["instrument"] == "BTCUSDT"
        assert detail["stop_loss"] == "49000"
        assert detail["take_profit"] == "52000"
        assert detail["notes"] == "Detail test trade"
        assert detail["is_closed"] is False

        missing_response = client.get(
            f"/api/v1/accounts/{account_id}/trades/{uuid.uuid4()}",
            headers=headers,
        )

        assert missing_response.status_code == 404

    finally:
        if trade is not None:
            db.delete(trade)

        if account is not None:
            db.delete(account)

        if user is not None:
            db.delete(user)

        db.commit()
        db.close()


def test_get_trade_detail_without_token_returns_401():
    response = client.get(
        f"/api/v1/accounts/{uuid.uuid4()}/trades/{uuid.uuid4()}",
    )

    assert response.status_code == 401
