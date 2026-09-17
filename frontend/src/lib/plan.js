/**
 * The trading plan as the client reads it.
 *
 * A plan is versioned server-side: publishing one closes the previous version,
 * so the limits in force at any past moment stay recoverable. Everything here
 * works on the list the API returns, newest version first.
 */

import { riskAmount } from "./trades";

// Without a plan or a profile the screens still need a yardstick; 2% per trade
// is the common retail rule, and every panel says when it is the one in use.
export const DEFAULT_RISK_LIMIT_PCT = 2;

/** The version with no end date — the one new trades are measured against. */
export const activePlan = (plans = []) => plans.find((plan) => !plan.valid_to) || null;

/**
 * Where the risk limit comes from, in order of how specific it is: the plan the
 * account committed to, then the older risk profile, then the fallback.
 */
export function riskLimit(plan, profile) {
  const planned = Number(plan?.max_risk_per_trade_pct);
  if (planned > 0) return { pct: planned, source: "plan", version: plan.version };

  const declared = Number(profile?.risk_per_trade_pct);
  if (declared > 0) return { pct: declared, source: "profile" };

  return { pct: DEFAULT_RISK_LIMIT_PCT, source: "default" };
}

const sameDay = (value, reference) => {
  if (!value) return false;
  const date = new Date(value);
  return (
    date.getFullYear() === reference.getFullYear() &&
    date.getMonth() === reference.getMonth() &&
    date.getDate() === reference.getDate()
  );
};

/**
 * Where the session stands right now.
 *
 * The daily loss is measured against the balance the day opened with, not the
 * one it has already shrunk to — otherwise a bad morning quietly widens the
 * budget it is spending.
 */
export function session(trades = [], balance, now = new Date()) {
  const closedToday = trades.filter((trade) => trade.is_closed && sameDay(trade.closed_at, now));
  const realized = closedToday.reduce((sum, trade) => sum + Number(trade.pnl || 0), 0);

  return {
    opened: trades.filter((trade) => sameDay(trade.opened_at, now)).length,
    closed: closedToday.length,
    realized,
    openingBalance: Number(balance || 0) - realized,
    openPositions: trades.filter((trade) => !trade.is_closed).length,
    // What the open book would lose if every stop were hit at once.
    exposedRisk: trades
      .filter((trade) => !trade.is_closed)
      .reduce((sum, trade) => sum + (riskAmount(trade) || 0), 0),
  };
}

const gauge = (key, used, limit, options = {}) => {
  const ratio = limit > 0 ? used / limit : 0;
  return {
    key,
    used,
    limit,
    ratio,
    state: ratio >= 1 ? "reached" : ratio >= 0.75 ? "near" : "ok",
    ...options,
  };
};

/**
 * The plan's limits as gauges: what has been used today against what was
 * allowed. Only the rules the plan actually set are returned — an unset limit
 * is not a limit of zero.
 */
export function planUsage(plan, trades = [], balance, now = new Date()) {
  if (!plan) return null;

  const state = session(trades, balance, now);
  const gauges = [];

  if (plan.max_trades_per_day) {
    gauges.push(gauge("tradesToday", state.opened, Number(plan.max_trades_per_day)));
  }

  if (plan.max_open_positions) {
    gauges.push(gauge("openPositions", state.openPositions, Number(plan.max_open_positions)));
  }

  const lossPct = Number(plan.max_daily_loss_pct);
  if (lossPct > 0 && state.openingBalance > 0) {
    gauges.push(
      gauge("dailyLoss", Math.max(0, -state.realized), (state.openingBalance * lossPct) / 100, {
        money: true,
        pct: lossPct,
      }),
    );
  }

  return {
    session: state,
    gauges,
    // One reached limit is the plan asking for the day to end.
    reached: gauges.filter((item) => item.state === "reached").map((item) => item.key),
  };
}

/**
 * What the trade being typed would break. Warnings only — a journal records the
 * trades that broke the plan too, and hiding them would defeat the point.
 */
export function planCheck(plan, draft, { trades = [], balance, riskPct = null, now = new Date() } = {}) {
  if (!plan) return [];

  const issues = [];
  const usage = planUsage(plan, trades, balance, now);

  if (plan.require_stop_loss && !(Number(draft.stop_loss) > 0)) {
    issues.push({ code: "ruleStopRequired", level: "bad" });
  }

  const allowed = plan.allowed_instruments || [];
  if (allowed.length && draft.instrument && !allowed.includes(draft.instrument)) {
    issues.push({ code: "ruleInstrumentOff", level: "warn", values: { symbol: draft.instrument } });
  }

  const limit = Number(plan.max_risk_per_trade_pct);
  if (riskPct !== null && limit > 0 && riskPct > limit) {
    const far = riskPct > limit * 2;
    issues.push({
      code: far ? "ruleRiskFarOver" : "ruleRiskOver",
      level: far ? "bad" : "warn",
      values: { pct: riskPct, limit },
    });
  }

  for (const item of usage.gauges) {
    if (item.state !== "reached") continue;
    if (item.key === "tradesToday") {
      issues.push({ code: "ruleTradesSpent", level: "warn", values: { count: item.limit } });
    }
    if (item.key === "openPositions") {
      issues.push({ code: "ruleBookFull", level: "warn", values: { count: item.limit } });
    }
    if (item.key === "dailyLoss") {
      issues.push({ code: "ruleDayLost", level: "bad" });
    }
  }

  return issues;
}

/**
 * The one-glance verdict a card can carry: which version is in force and
 * whether today has run into it. Null when the account has no plan at all.
 */
export function planBadge(plans = [], trades = [], balance, now = new Date()) {
  const plan = activePlan(plans);
  if (!plan) return null;

  const usage = planUsage(plan, trades, balance, now);
  return {
    version: plan.version,
    state: usage.reached.length
      ? "reached"
      : usage.gauges.some((item) => item.state === "near")
        ? "near"
        : "ok",
  };
}

/** The rules in the order every plan surface lists them. */
export const RULES = [
  { field: "max_risk_per_trade_pct", label: "ruleRisk", kind: "pct" },
  { field: "max_daily_loss_pct", label: "ruleDailyLoss", kind: "pct" },
  { field: "max_trades_per_day", label: "ruleTradesPerDay", kind: "count" },
  { field: "max_open_positions", label: "ruleOpenPositions", kind: "count" },
  { field: "require_stop_loss", label: "ruleStopField", kind: "bool" },
  { field: "allowed_instruments", label: "ruleInstruments", kind: "list" },
  { field: "allowed_setups", label: "ruleSetups", kind: "list" },
];

const same = (kind, left, right) => {
  if (kind === "list") return JSON.stringify(left || []) === JSON.stringify(right || []);
  if (kind === "bool") return Boolean(left) === Boolean(right);
  if (left === null || left === undefined || right === null || right === undefined) return left === right;
  return Number(left) === Number(right);
};

/** What changed between one version and the one before it. */
export function planDiff(plan, previous) {
  if (!plan || !previous) return [];

  return RULES.filter((rule) => !same(rule.kind, plan[rule.field], previous[rule.field])).map((rule) => ({
    ...rule,
    from: previous[rule.field],
    to: plan[rule.field],
  }));
}
