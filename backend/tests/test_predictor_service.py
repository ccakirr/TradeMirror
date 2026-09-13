from backend.app.schemas.predictor import PredictorRequest, PredictorResponse
from backend.app.services.predictor import classify_risk, predict


request = PredictorRequest(
    starting_capital=1000.0,
    account_age_months=12,
    instrument="forex",
    risk_per_trade_pct=1.0,
    trades_per_month=20,
    uses_stop_loss=1,
    avg_win_hold_days=3,
    avg_loss_hold_days=2.5,
    diversification=4,
    follows_plan=8,
    position_sizing_discipline=7.5
)


def test_predict_returns_valid_risk_assessment():
    response = predict(request)

    assert isinstance(response, PredictorResponse)
    assert 0 <= response.score <= 1
    assert response.risk_class in ["low", "medium", "high"]
    assert response.threshold == 0.4166
    assert response.model_version == "product_v1"


def test_classify_low_risk():
    assert classify_risk(0.20) == "low"


def test_classify_medium_risk():
    assert classify_risk(0.50) == "medium"


def test_classify_threshold_as_medium():
    assert classify_risk(0.4166) == "medium"


def test_classify_high_risk():
    assert classify_risk(0.80) == "high"


def test_classify_high_threshold_as_high():
    assert classify_risk(0.70) == "high"