import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

from ..app.db import SessionLocal
from ..app.main import app
from ..app.models.trade import Trade
from ..app.models.trading_accounts import TradingAccount
from ..app.models.user import User
from ..app.services.risk_report import compose_risk_report


client = TestClient(app)

OPENED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_account(balance="10000"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        initial_balance=Decimal(balance),
        current_balance=Decimal(balance),
    )


def make_trade(**overrides):
    trade = {
        "id": uuid.uuid4(),
        "instrument": "BTCUSDT",
        "is_long": True,
        "is_closed": False,
        "entry_price": Decimal("50000"),
        "exit_price": None,
        "position_size": Decimal("0.1"),
        "stop_loss": Decimal("49000"),
        "take_profit": Decimal("52000"),
        "opened_at": OPENED_AT,
        "closed_at": None,
        "pnl": None,
    }
    trade.update(overrides)
    return SimpleNamespace(**trade)


def make_profile(**overrides):
    profile = {
        "instrument": "crypto",
        "risk_per_trade_pct": Decimal("2"),
        "trades_per_month": Decimal("20"),
        "avg_win_hold_days": Decimal("4"),
        "avg_loss_hold_days": Decimal("2"),
        "diversification": Decimal("3"),
        "follows_plan": Decimal("7"),
        "position_sizing_discipline": Decimal("7"),
    }
    profile.update(overrides)
    return SimpleNamespace(**profile)


def make_assessment(risk_class="low", score="0.12", stage="entry"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        stage=stage,
        score=Decimal(score),
        risk_class=risk_class,
        threshold=Decimal("0.4166"),
        model_version="product_v1",
        created_at=OPENED_AT,
    )


def codes(report):
    return [finding.code for finding in report.findings]


def level_of(report, code):
    return next(
        finding.level for finding in report.findings if finding.code == code
    )


def test_planned_trade_reads_as_low_risk():
    report = compose_risk_report(
        make_account(),
        make_trade(),
        make_profile(),
        [make_assessment()],
    )

    # 1000 * 0.1 = 100 risked on a 10.000 account: 1% against a 2% limit.
    assert report.risk_amount == Decimal("100.00")
    assert report.risk_pct == Decimal("1.00")
    assert report.risk_limit_pct == Decimal("2.00")
    assert report.reward_risk == Decimal("2.00")
    assert report.notional == Decimal("5000.00")
    assert report.exposure_pct == Decimal("50.00")
    assert report.risk_class == "low"
    assert "stop_set" in codes(report)
    assert "risk_within_limit" in codes(report)
    assert "rr_strong" in codes(report)
    assert "exposure_high" not in codes(report)


def test_missing_stop_has_no_risk_numbers_and_lifts_the_class():
    report = compose_risk_report(
        make_account(),
        make_trade(stop_loss=None, take_profit=None),
        make_profile(),
        [make_assessment()],
    )

    assert report.risk_amount is None
    assert report.risk_pct is None
    assert report.reward_risk is None
    assert level_of(report, "stop_missing") == "bad"
    assert "target_missing" in codes(report)
    assert report.risk_class == "medium"


def test_oversized_risk_and_exposure_are_flagged():
    report = compose_risk_report(
        make_account("1000"),
        make_trade(position_size=Decimal("0.1"), stop_loss=Decimal("45000")),
        make_profile(),
        [make_assessment()],
    )

    # 5000 * 0.1 = 500 risked on a 1.000 account.
    assert report.risk_pct == Decimal("50.00")
    assert level_of(report, "risk_far_above_limit") == "bad"
    assert level_of(report, "exposure_extreme") == "bad"
    assert report.risk_class == "high"


def test_a_zero_limit_leaves_no_room_for_risk():
    report = compose_risk_report(
        make_account(),
        make_trade(),
        make_profile(risk_per_trade_pct=Decimal("0")),
        [make_assessment()],
    )

    assert level_of(report, "risk_far_above_limit") == "bad"


def test_short_trade_risk_uses_absolute_stop_distance():
    report = compose_risk_report(
        make_account(),
        make_trade(
            is_long=False,
            stop_loss=Decimal("51000"),
            take_profit=Decimal("48000"),
        ),
        make_profile(),
        [make_assessment()],
    )

    assert report.risk_amount == Decimal("100.00")
    assert report.reward_risk == Decimal("2.00")


def test_thin_reward_risk_is_a_warning():
    report = compose_risk_report(
        make_account(),
        make_trade(take_profit=Decimal("50500")),
        make_profile(),
        [make_assessment()],
    )

    assert report.reward_risk == Decimal("0.50")
    assert level_of(report, "rr_negative") == "bad"


def test_target_hit_closes_the_report_with_the_plan_honored():
    # The balance already carries the +200 this trade won.
    report = compose_risk_report(
        make_account("10200"),
        make_trade(
            is_closed=True,
            exit_price=Decimal("52000"),
            closed_at=OPENED_AT + timedelta(days=3),
            pnl=Decimal("200"),
        ),
        make_profile(),
        [make_assessment(stage="exit")],
    )

    assert level_of(report, "exit_target") == "good"
    # The winner's own profit is not counted as balance it was risked against.
    assert report.risk_pct == Decimal("1.00")
    assert report.r_multiple == Decimal("2.00")
    assert report.holding_days == Decimal("3.0")
    assert report.risk_class == "low"


def test_manual_exit_beyond_the_stop_is_flagged_twice():
    report = compose_risk_report(
        make_account(),
        make_trade(
            is_closed=True,
            exit_price=Decimal("48000"),
            closed_at=OPENED_AT + timedelta(days=1),
            pnl=Decimal("-200"),
        ),
        make_profile(),
        [make_assessment(stage="exit")],
    )

    assert level_of(report, "exit_manual") == "warn"
    assert level_of(report, "loss_exceeded_stop") == "bad"
    assert report.r_multiple == Decimal("-2.00")


def test_loss_held_past_the_account_average():
    report = compose_risk_report(
        make_account(),
        make_trade(
            is_closed=True,
            exit_price=Decimal("49000"),
            closed_at=OPENED_AT + timedelta(days=9),
            pnl=Decimal("-100"),
        ),
        make_profile(avg_loss_hold_days=Decimal("2")),
        [make_assessment(stage="exit")],
    )

    assert level_of(report, "held_loss_too_long") == "warn"
    assert report.holding_days == Decimal("9.0")


def test_winner_cut_far_below_the_account_average():
    report = compose_risk_report(
        make_account(),
        make_trade(
            is_closed=True,
            exit_price=Decimal("50500"),
            closed_at=OPENED_AT + timedelta(hours=6),
            pnl=Decimal("50"),
        ),
        make_profile(avg_win_hold_days=Decimal("4")),
        [make_assessment(stage="exit")],
    )

    assert level_of(report, "cut_win_early") == "info"


def test_without_a_profile_the_default_limit_is_used():
    report = compose_risk_report(make_account(), make_trade(), None, [])

    assert report.risk_limit_pct == Decimal("2.00")
    assert report.score is None
    assert "profile_missing" in codes(report)
    assert "model_missing" in codes(report)


def test_high_model_class_carries_the_report():
    report = compose_risk_report(
        make_account(),
        make_trade(),
        make_profile(),
        [make_assessment(risk_class="high", score="0.91")],
    )

    assert level_of(report, "model_high") == "bad"
    assert report.score == Decimal("0.91")
    assert report.model_version == "product_v1"
    assert report.risk_class == "high"


def test_the_newest_assessment_wins():
    entry = make_assessment(risk_class="high", score="0.91")
    exit_stage = make_assessment(risk_class="low", score="0.10", stage="exit")
    exit_stage.created_at = OPENED_AT + timedelta(days=1)

    report = compose_risk_report(
        make_account(),
        make_trade(),
        make_profile(),
        [entry, exit_stage],
    )

    assert report.model_stage == "exit"
    assert report.score == Decimal("0.10")


def test_risk_report_api_returns_the_report_for_the_owner():
    email = f"risk-report-{uuid.uuid4()}@example.com"
    password = "test1234"

    db = SessionLocal()
    user = None
    account = None
    trade = None

    try:
        register_response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )

        assert register_response.status_code == 201

        user = db.get(User, UUID(register_response.json()["id"]))

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

        assert login_response.status_code == 200

        headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        account_response = client.post(
            "/api/v1/accounts/",
            headers=headers,
            json={"name": "Risk Report Account", "initial_balance": 10000},
        )

        assert account_response.status_code == 200

        account_id = account_response.json()["id"]
        account = db.get(TradingAccount, UUID(account_id))

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
            },
        )

        assert trade_response.status_code == 201

        trade_id = trade_response.json()["id"]
        trade = db.get(Trade, UUID(trade_id))

        report_response = client.get(
            f"/api/v1/accounts/{account_id}/trades/{trade_id}/risk-report",
            headers=headers,
        )

        assert report_response.status_code == 200

        report = report_response.json()

        assert report["trade_id"] == trade_id
        assert report["risk_class"] in {"low", "medium", "high"}
        assert report["risk_amount"] == "100"
        assert report["risk_pct"] == "1"
        assert report["reward_risk"] == "2"
        assert report["findings"]
        assert {"stop_set", "rr_strong"} <= {
            finding["code"] for finding in report["findings"]
        }

        missing_response = client.get(
            f"/api/v1/accounts/{account_id}/trades/{uuid.uuid4()}/risk-report",
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


def test_risk_report_without_token_returns_401():
    response = client.get(
        f"/api/v1/accounts/{uuid.uuid4()}/trades/{uuid.uuid4()}/risk-report",
    )

    assert response.status_code == 401

