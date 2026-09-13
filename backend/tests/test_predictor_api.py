from fastapi.testclient import TestClient
from ..app.main import app

client = TestClient(app)


def test_predict_risk_with_valid_payload():
    payload = {
        "starting_capital": 10000,
        "account_age_months": 12,
        "instrument": "forex",
        "risk_per_trade_pct": 1.0,
        "trades_per_month": 20,
        "uses_stop_loss": 1,
        "avg_win_hold_days": 2.5,
        "avg_loss_hold_days": 3.8,
        "diversification": 4,
        "follows_plan": 8.0,
        "position_sizing_discipline": 7.5
    }

    response = client.post(
        "/api/v1/predict/",
        json=payload
    )

    assert response.status_code == 200

    result = response.json()

    assert "score" in result
    assert "risk_class" in result
    assert "threshold" in result
    assert "model_version" in result

    assert 0 <= result["score"] <= 1
    assert result["risk_class"] in ["low", "medium", "high"]
    assert result["threshold"] == 0.4166
    assert result["model_version"] == "product_v1"


def test_predict_risk_missing_field_returns_422():
    payload = {
        "account_age_months": 12,
        "instrument": "forex",
        "risk_per_trade_pct": 1.0,
        "trades_per_month": 20,
        "uses_stop_loss": 1,
        "avg_win_hold_days": 2.5,
        "avg_loss_hold_days": 3.8,
        "diversification": 4,
        "follows_plan": 8.0,
        "position_sizing_discipline": 7.5
    }

    response = client.post(
        "/api/v1/predict/",
        json=payload
    )

    assert response.status_code == 422


def test_predict_risk_invalid_instrument_returns_422():
    payload = {
        "starting_capital": 10000,
        "account_age_months": 12,
        "instrument": "gold",
        "risk_per_trade_pct": 1.0,
        "trades_per_month": 20,
        "uses_stop_loss": 1,
        "avg_win_hold_days": 2.5,
        "avg_loss_hold_days": 3.8,
        "diversification": 4,
        "follows_plan": 8.0,
        "position_sizing_discipline": 7.5
    }

    response = client.post(
        "/api/v1/predict/",
        json=payload
    )

    assert response.status_code == 422
