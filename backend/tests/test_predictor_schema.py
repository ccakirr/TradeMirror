import pytest
from pydantic import ValidationError

from backend.app.schemas.predictor import PredictorRequest


def valid_payload():
    return {
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


def test_valid_predictor_request():
    request = PredictorRequest(**valid_payload())

    assert request.instrument == "forex"
    assert request.starting_capital == 10000


def test_negative_starting_capital_is_rejected():
    payload = valid_payload()
    payload["starting_capital"] = -100

    with pytest.raises(ValidationError):
        PredictorRequest(**payload)


def test_invalid_instrument_is_rejected():
    payload = valid_payload()
    payload["instrument"] = "gold"

    with pytest.raises(ValidationError):
        PredictorRequest(**payload)
