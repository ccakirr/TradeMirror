import { decimal, money } from "../lib/format";

/**
 * The mirror, held up before the decision instead of after it: what the trade
 * being typed would actually risk, next to the limit the plan set.
 *
 * It never blocks the submit — a journal records what happened, including the
 * trades that broke the plan.
 */
export default function RiskPreview({ t, lang, draft, balance, limitPct }) {
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
  const tone = risk === null ? "warn" : overBy === null ? "" : overBy > 2 ? "bad" : overBy > 1 ? "warn" : "good";

  const notes = [];
  if (risk === null) {
    notes.push({ tone: "warn", text: t("previewNoStop") });
  } else if (riskPct !== null) {
    const values = { pct: decimal(riskPct, lang), limit: decimal(limit, lang) };
    notes.push(
      overBy > 1
        ? { tone: overBy > 2 ? "bad" : "warn", text: t("previewOverLimit", values) }
        : { tone: "good", text: t("previewWithinLimit", values) },
    );
  }
  if (reward !== null && reward < 1) notes.push({ tone: "warn", text: t("previewThinReward") });

  return (
    <div className={`risk-preview ${tone}`} role="status" aria-live="polite">
      <p className="eyebrow">{t("thisTrade")}</p>

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
