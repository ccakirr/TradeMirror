/** Rolls a trade list into the numbers the dashboard, cards and detail header all show. */
export function summarize(trades = []) {
  const closed = trades.filter((trade) => trade.is_closed);
  const wins = closed.filter((trade) => Number(trade.pnl) > 0).length;
  const realized = closed.reduce((sum, trade) => sum + Number(trade.pnl || 0), 0);

  return {
    total: trades.length,
    open: trades.length - closed.length,
    closed: closed.length,
    wins,
    losses: closed.length - wins,
    realized,
    winRate: closed.length ? (wins / closed.length) * 100 : null,
  };
}

/** Reward-to-risk from the planned stop and target, when both were recorded. */
export function riskReward(trade) {
  const entry = Number(trade.entry_price);
  const stop = Number(trade.stop_loss);
  const target = Number(trade.take_profit);
  if (!trade.stop_loss || !trade.take_profit || !entry) return null;

  const risk = Math.abs(entry - stop);
  const reward = Math.abs(target - entry);
  if (!risk) return null;
  return reward / risk;
}

/** Return on the position itself, independent of account size. */
export function tradeReturnPercent(trade) {
  if (!trade.is_closed || trade.pnl === null || trade.pnl === undefined) return null;
  const invested = Number(trade.entry_price) * Number(trade.position_size);
  if (!invested) return null;
  return (Number(trade.pnl) / invested) * 100;
}

/** What the position costs to open — entry times size. */
export function notional(trade) {
  const value = Number(trade.entry_price) * Number(trade.position_size);
  return value || null;
}

/** Currency the plan put at risk: the loss the stop would have taken. */
export function riskAmount(trade) {
  if (!trade.stop_loss) return null;
  const distance = Math.abs(Number(trade.entry_price) - Number(trade.stop_loss));
  const risk = distance * Number(trade.position_size);
  return risk || null;
}

/** Result in units of planned risk — +2R means twice what the stop was willing to lose. */
export function rMultiple(trade) {
  const risk = riskAmount(trade);
  if (!trade.is_closed || risk === null || trade.pnl === null || trade.pnl === undefined) return null;
  return Number(trade.pnl) / risk;
}

/** How long the position was live, in milliseconds; null while it is still open. */
export function holdingMs(trade) {
  if (!trade.is_closed || !trade.closed_at) return null;
  const span = new Date(trade.closed_at) - new Date(trade.opened_at);
  return Number.isFinite(span) && span >= 0 ? span : null;
}

/**
 * Whether the exit honored the plan: "target", "stop" or "manual".
 * Fills rarely land exactly on a level, so anything within 0.1% of entry counts as a hit.
 */
export function exitVerdict(trade) {
  if (!trade.is_closed || trade.exit_price === null || trade.exit_price === undefined) return null;

  const exit = Number(trade.exit_price);
  const tolerance = Math.abs(Number(trade.entry_price)) * 0.001;

  if (trade.take_profit && Math.abs(exit - Number(trade.take_profit)) <= tolerance) return "target";
  if (trade.stop_loss && Math.abs(exit - Number(trade.stop_loss)) <= tolerance) return "stop";
  return "manual";
}

/**
 * The balance each trade's risk was actually taken against.
 *
 * An account's balance only moves when a position closes, so walking the closed
 * trades backwards from today's balance recovers what it was worth before each
 * one settled. Judging a loss against the balance it shrank would flatter it.
 */
export function riskLedger(trades = [], currentBalance) {
  const ledger = new Map();
  const balance = Number(currentBalance || 0);

  const closed = trades
    .filter((trade) => trade.is_closed && trade.closed_at)
    .sort((a, b) => new Date(b.closed_at) - new Date(a.closed_at));

  let running = balance;
  for (const trade of closed) {
    running -= Number(trade.pnl || 0);
    ledger.set(trade.id, running);
  }

  // Open positions are still being carried by the account as it stands now.
  for (const trade of trades) {
    if (!ledger.has(trade.id)) ledger.set(trade.id, balance);
  }

  return ledger;
}

/** Planned risk as a share of the balance behind it — null without a stop. */
export function riskPercent(trade, balance) {
  const risk = riskAmount(trade);
  const size = Number(balance || 0);
  if (risk === null || size <= 0) return null;
  return (risk / size) * 100;
}

const average = (values) =>
  values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;

/**
 * The behavior behind the numbers: how often a stop was set, how often the exit
 * honored the plan, and how the risk taken compares with the plan's limit.
 * Every metric is null until there is data for it — missing is never zero.
 */
export function behaviorSummary(trades = [], { balance, limitPct } = {}) {
  const ledger = riskLedger(trades, balance);
  const closed = trades.filter((trade) => trade.is_closed);
  const withStop = trades.filter((trade) => trade.stop_loss);

  // Only trades that had a plan can be judged against one.
  const planned = closed.filter((trade) => trade.stop_loss || trade.take_profit);
  const honored = planned.filter((trade) => ["target", "stop"].includes(exitVerdict(trade)));

  const risks = withStop
    .map((trade) => riskPercent(trade, ledger.get(trade.id)))
    .filter((value) => value !== null);

  const limit = Number(limitPct);
  const breaches = limit > 0 ? risks.filter((value) => value > limit).length : 0;

  return {
    total: trades.length,
    closed: closed.length,
    stopUsage: trades.length ? (withStop.length / trades.length) * 100 : null,
    missingStops: trades.length - withStop.length,
    adherence: planned.length ? (honored.length / planned.length) * 100 : null,
    plannedCount: planned.length,
    avgRisk: average(risks),
    riskSample: risks.length,
    breaches,
    avgReward: average(trades.map(riskReward).filter((value) => value !== null)),
    avgR: average(closed.map(rMultiple).filter((value) => value !== null)),
  };
}
