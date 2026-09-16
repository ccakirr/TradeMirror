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
