from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.risk_assessment import RiskAssessment
from ..models.risk_profile import TradingAccountRiskProfile
from ..models.trade import Trade
from ..models.trading_accounts import TradingAccount
from ..models.trading_plan import TradingPlan
from ..models.user import User
from ..schemas.risk_report import RiskReportFinding, RiskReportResponse


# Without a plan or a saved risk profile the report still needs a yardstick; 2%
# per trade is the common retail rule of thumb, and the client says it is the
# fallback being used.
DEFAULT_RISK_LIMIT_PCT = Decimal("2")

# A position worth more than the account means leverage. Normal on forex and
# futures, worth naming anyway — the reader decides whether it was intended.
EXPOSURE_WARN_PCT = Decimal("100")
EXPOSURE_BAD_PCT = Decimal("300")

# Fills rarely land exactly on a level, so an exit within 0.1% of the planned
# price counts as that level being hit. Mirrors the client's exitVerdict().
EXIT_TOLERANCE = Decimal("0.001")

# Slippage past the stop is normal; losing 5% more than planned is not.
STOP_OVERSHOOT = Decimal("1.05")

# How far a hold may drift from the account's own average before it is a habit
# worth pointing at rather than noise.
LONG_LOSS_FACTOR = Decimal("1.5")
SHORT_WIN_FACTOR = Decimal("0.5")

LEVEL_POINTS = {"good": 0, "info": 0, "warn": 1, "bad": 2}
MODEL_POINTS = {"low": 0, "medium": 2, "high": 4}
MEDIUM_AT = 2
HIGH_AT = 4

SECONDS_PER_DAY = Decimal(86400)


def _round(value: Decimal | None, places: str) -> Decimal | None:
    return None if value is None else value.quantize(Decimal(places))


def _text(value: Decimal | None) -> str:
    return "" if value is None else format(value.normalize(), "f")


def _balance(account: TradingAccount, trade: Trade) -> Decimal:
    """The account as it stood when the risk was taken.

    A closed trade has already moved the balance, and judging a loss against
    the balance it shrank would flatter every losing trade, so its own result
    is added back. A wiped account falls back to where it started.
    """
    balance = Decimal(account.current_balance)

    if trade.is_closed and trade.pnl is not None:
        balance -= Decimal(trade.pnl)

    return balance if balance > 0 else Decimal(account.initial_balance)


def _risk_amount(trade: Trade) -> Decimal | None:
    """Currency the plan put at risk: the loss the stop would have taken."""
    if trade.stop_loss is None:
        return None

    distance = abs(Decimal(trade.entry_price) - Decimal(trade.stop_loss))
    return distance * Decimal(trade.position_size)


def _reward_risk(trade: Trade) -> Decimal | None:
    if trade.stop_loss is None or trade.take_profit is None:
        return None

    entry = Decimal(trade.entry_price)
    risk = abs(entry - Decimal(trade.stop_loss))

    if risk == 0:
        return None

    return abs(Decimal(trade.take_profit) - entry) / risk


def _holding_days(trade: Trade) -> Decimal | None:
    if not trade.is_closed or trade.closed_at is None:
        return None

    opened = trade.opened_at
    closed = trade.closed_at

    if opened.tzinfo is None:
        opened = opened.replace(tzinfo=timezone.utc)
    if closed.tzinfo is None:
        closed = closed.replace(tzinfo=timezone.utc)

    seconds = Decimal((closed - opened).total_seconds())
    return max(Decimal(0), seconds / SECONDS_PER_DAY)


def _exit_verdict(trade: Trade) -> str | None:
    """Whether the exit honored the plan: "target", "stop" or "manual"."""
    if not trade.is_closed or trade.exit_price is None:
        return None

    exit_price = Decimal(trade.exit_price)
    tolerance = abs(Decimal(trade.entry_price)) * EXIT_TOLERANCE

    if (
        trade.take_profit is not None
        and abs(exit_price - Decimal(trade.take_profit)) <= tolerance
    ):
        return "target"

    if (
        trade.stop_loss is not None
        and abs(exit_price - Decimal(trade.stop_loss)) <= tolerance
    ):
        return "stop"

    return "manual"


def _pick_assessment(
    assessments: list[RiskAssessment],
) -> RiskAssessment | None:
    """The newest score is the one that saw the most of the trade."""
    if not assessments:
        return None

    return sorted(assessments, key=lambda item: item.created_at)[-1]


def compose_risk_report(
    account: TradingAccount,
    trade: Trade,
    profile: TradingAccountRiskProfile | None,
    assessments: list[RiskAssessment],
    plan: TradingPlan | None = None,
) -> RiskReportResponse:
    """Turn one trade into an explainable risk report.

    Every finding is a rule the reader can re-check by hand; the model score is
    reported next to them, never as the verdict on its own.
    """
    findings: list[RiskReportFinding] = []

    def add(code: str, level: str, **values: Decimal | None) -> None:
        findings.append(
            RiskReportFinding(
                code=code,
                level=level,
                values={name: _text(value) for name, value in values.items()},
            )
        )

    balance = _balance(account, trade)
    notional = Decimal(trade.entry_price) * Decimal(trade.position_size)
    exposure_pct = notional / balance * 100
    risk_amount = _risk_amount(trade)
    risk_pct = None if risk_amount is None else risk_amount / balance * 100
    reward_risk = _reward_risk(trade)
    holding_days = _holding_days(trade)
    # The plan the trade was opened under judges it, whatever the account has
    # committed to since. Only an account with no plan falls back to the
    # profile, and then to the default.
    if plan is not None:
        limit_pct = Decimal(plan.max_risk_per_trade_pct)
    elif profile is not None:
        limit_pct = Decimal(profile.risk_per_trade_pct)
    else:
        limit_pct = DEFAULT_RISK_LIMIT_PCT

    r_multiple = None
    if trade.is_closed and trade.pnl is not None and risk_amount:
        r_multiple = Decimal(trade.pnl) / risk_amount

    # 1 — the stop, and what it puts at risk.
    if risk_amount is None:
        add("stop_missing", "bad")
    else:
        add("stop_set", "good", risk=_round(risk_amount, "0.01"))

        rounded_pct = _round(risk_pct, "0.01")
        rounded_limit = _round(limit_pct, "0.01")

        # A limit of zero is a real answer, not a missing one: every cent of
        # risk is then above what the plan allows.
        if risk_pct > limit_pct * 2:
            add("risk_far_above_limit", "bad", pct=rounded_pct, limit=rounded_limit)
        elif risk_pct > limit_pct:
            add("risk_above_limit", "warn", pct=rounded_pct, limit=rounded_limit)
        else:
            add("risk_within_limit", "good", pct=rounded_pct, limit=rounded_limit)

    # 2 — what the plan expected in return.
    if trade.take_profit is None:
        add("target_missing", "info")
    elif reward_risk is not None:
        ratio = _round(reward_risk, "0.01")
        if reward_risk >= 2:
            add("rr_strong", "good", ratio=ratio)
        elif reward_risk >= 1:
            add("rr_thin", "warn", ratio=ratio)
        else:
            add("rr_negative", "bad", ratio=ratio)

    # 3 — position size against the account behind it.
    if exposure_pct > EXPOSURE_BAD_PCT:
        add("exposure_extreme", "bad", pct=_round(exposure_pct, "0.01"))
    elif exposure_pct > EXPOSURE_WARN_PCT:
        add("exposure_high", "warn", pct=_round(exposure_pct, "0.01"))

    # 4 — how the position actually ended.
    verdict = _exit_verdict(trade)

    if verdict == "target":
        add("exit_target", "good")
    elif verdict == "stop":
        add("exit_stop", "good")
    elif verdict == "manual":
        if trade.stop_loss is None and trade.take_profit is None:
            add("exit_manual_no_plan", "info")
        else:
            add("exit_manual", "warn")

    loss = (
        -Decimal(trade.pnl)
        if trade.is_closed and trade.pnl is not None and trade.pnl < 0
        else None
    )

    if loss is not None and risk_amount is not None and loss > risk_amount * STOP_OVERSHOOT:
        add(
            "loss_exceeded_stop",
            "bad",
            loss=_round(loss, "0.01"),
            planned=_round(risk_amount, "0.01"),
        )

    # 5 — the hold, read against this account's own averages.
    if profile is not None and holding_days is not None and trade.pnl is not None:
        average_loss_hold = Decimal(profile.avg_loss_hold_days)
        average_win_hold = Decimal(profile.avg_win_hold_days)

        if (
            trade.pnl < 0
            and average_loss_hold > 0
            and holding_days > average_loss_hold * LONG_LOSS_FACTOR
        ):
            add(
                "held_loss_too_long",
                "warn",
                days=_round(holding_days, "0.1"),
                average=_round(average_loss_hold, "0.1"),
            )
        elif (
            trade.pnl > 0
            and average_win_hold > 0
            and holding_days < average_win_hold * SHORT_WIN_FACTOR
        ):
            add(
                "cut_win_early",
                "info",
                days=_round(holding_days, "0.1"),
                average=_round(average_win_hold, "0.1"),
            )

    # 6 — the model, last: it comments on the account's habits, not this fill.
    assessment = _pick_assessment(assessments)

    if plan is not None:
        add(
            "plan_version",
            "info",
            version=Decimal(plan.version),
            limit=_round(limit_pct, "0.01"),
        )
    elif profile is None:
        add("profile_missing", "info", limit=_round(limit_pct, "0.01"))

    if assessment is None:
        add("model_missing", "info")
    else:
        score = _round(Decimal(assessment.score), "0.001")
        threshold = _round(Decimal(assessment.threshold), "0.001")
        add(
            f"model_{assessment.risk_class}",
            {"low": "good", "medium": "warn", "high": "bad"}[assessment.risk_class],
            score=score,
            threshold=threshold,
        )

    # The model speaks once: its finding carries the class, its weight comes
    # from MODEL_POINTS rather than being counted twice as a plain finding.
    points = sum(
        LEVEL_POINTS[finding.level]
        for finding in findings
        if not finding.code.startswith("model_")
    )

    if assessment is not None:
        points += MODEL_POINTS[assessment.risk_class]

    risk_class = "high" if points >= HIGH_AT else "medium" if points >= MEDIUM_AT else "low"

    return RiskReportResponse(
        trade_id=trade.id,
        generated_at=datetime.now(timezone.utc),
        risk_class=risk_class,
        score=None if assessment is None else Decimal(assessment.score),
        threshold=None if assessment is None else Decimal(assessment.threshold),
        model_version=None if assessment is None else assessment.model_version,
        model_stage=None if assessment is None else assessment.stage,
        risk_amount=_round(risk_amount, "0.01"),
        risk_pct=_round(risk_pct, "0.01"),
        risk_limit_pct=_round(limit_pct, "0.01"),
        reward_risk=_round(reward_risk, "0.01"),
        notional=_round(notional, "0.01"),
        exposure_pct=_round(exposure_pct, "0.01"),
        r_multiple=_round(r_multiple, "0.01"),
        holding_days=_round(holding_days, "0.1"),
        findings=findings,
    )


def get_risk_report(
    db: Session,
    current_user: User,
    account_id: UUID,
    trade_id: UUID,
) -> RiskReportResponse:
    account = db.get(TradingAccount, account_id)
    trade = db.get(Trade, trade_id)

    if account is None or account.user_id != current_user.id:
        raise ValueError("Trading account not found")

    if trade is None or trade.account_id != account.id:
        raise ValueError("Trade not found")

    profile = db.scalar(
        select(TradingAccountRiskProfile).where(
            TradingAccountRiskProfile.account_id == account.id
        )
    )

    assessments = list(
        db.scalars(
            select(RiskAssessment)
            .where(RiskAssessment.trade_id == trade.id)
            .order_by(RiskAssessment.created_at.asc())
        ).all()
    )

    return compose_risk_report(account, trade, profile, assessments, trade.trading_plan)
