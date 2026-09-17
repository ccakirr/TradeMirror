import { decimal, money } from "../lib/format";
import { planCheck } from "../lib/plan";

/**
 * The mirror, held up before the decision instead of after it: what the trade
 * being typed would actually risk, next to the limits the plan set — including
 * the ones the day has already spent.
 *
 * It never blocks the submit — a journal records what happened, including the
 * trades that broke the plan.
 */
export default function RiskPreview({ t, lang, draft, balance, limitPct, plan = null, trades = [] }) {
  const entry = Number(draft.entry_price);
  const size = Number(draft.position_size);
  const stop = Number(draft.stop_loss);
  const target = Number(draft.take_profit);
  const account = Number(balance || 0);

  // Nothing to reflect until there is a position to measure.
  if (!(entry > 0) || !(size > 0)) return null;

  const notional = entry * size;
  const risk = stop > 0 ? Math.abs(entry - stop) * size : null;
  const riskPct = risk !== null && account > 0 ? (risk / account) * 100 : null;
  const reward = stop > 0 && target > 0 ? Math.abs(target - entry) / Math.abs(entry - stop) : null;

  const limit = Number(limitPct) || 0;
  const overBy = riskPct !== null && limit > 0 ? riskPct / limit : null;

  const issues = planCheck(plan, draft, { trades, balance: account, riskPct });
  const worst = issues.some((issue) => issue.level === "bad")
    ? "bad"
    : issues.length
      ? "warn"
      : null;

  const tone =
    worst ||
    (risk === null ? "warn" : overBy === null ? "" : overBy > 2 ? "bad" : overBy > 1 ? "warn" : "good");

  // Numbers reach the copy already written in the reader's locale.
  const say = (issue) =>
    t(
      issue.code,
      Object.fromEntries(
        Object.entries(issue.values || {}).map(([key, value]) => [
          key,
          typeof value === "number" && key !== "count" ? decimal(value, lang) : value,
        ]),
      ),
    );

  const notes = [];
  const flagged = issues.some((issue) => issue.code.startsWith("ruleRisk"));

  if (risk === null) {
    // A plan that requires a stop says it more sharply, just below.
    if (!plan?.require_stop_loss) notes.push({ tone: "warn", text: t("previewNoStop") });
  } else if (riskPct !== null && !flagged) {
    // With a plan the breach is reported as a broken rule below; without one the
    // limit is still worth measuring against.
    const values = { pct: decimal(riskPct, lang), limit: decimal(limit, lang) };
    notes.push(
      overBy > 1
        ? { tone: overBy > 2 ? "bad" : "warn", text: t("previewOverLimit", values) }
        : { tone: "good", text: t("previewWithinLimit", values) },
    );
  }

  for (const issue of issues) notes.push({ tone: issue.level, text: say(issue) });
  if (reward !== null && reward < 1) notes.push({ tone: "warn", text: t("previewThinReward") });

  return (
    <div className={`risk-preview ${tone}`} role="status" aria-live="polite">
      <p className="eyebrow">
        {t("thisTrade")}
        {plan && <span className="preview-plan">{t("againstPlan", { version: plan.version })}</span>}
      </p>

      <dl className="risk-preview-cells">
        <div>
          <dt>{t("riskAtStop")}</dt>
          <dd className={tone}>
            {risk === null ? "—" : money(risk, lang)}
            {riskPct !== null && <em>{decimal(riskPct, lang)}%</em>}
          </dd>
        </div>
        <div>
          <dt>{t("planLimit")}</dt>
          <dd>{limit > 0 ? `${decimal(limit, lang)}%` : "—"}</dd>
        </div>
        <div>
          <dt>{t("riskReward")}</dt>
          <dd>{reward === null ? "—" : `${decimal(reward, lang)} : 1`}</dd>
        </div>
        <div>
          <dt>{t("positionValue")}</dt>
          <dd>{money(notional, lang)}</dd>
        </div>
      </dl>

      {notes.map((note) => (
        <p className={`risk-preview-note ${note.tone}`} key={note.text}>
          {note.text}
        </p>
      ))}
    </div>
  );
}
