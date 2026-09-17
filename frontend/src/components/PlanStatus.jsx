import { decimal, money, shortDate } from "../lib/format";
import { planUsage } from "../lib/plan";
import { Button } from "./ui";

const LABELS = {
  tradesToday: "gaugeTradesToday",
  openPositions: "gaugeOpenPositions",
  dailyLoss: "gaugeDailyLoss",
};

const TONES = { ok: "positive", near: "caution", reached: "negative" };

function Gauge({ gauge, t, lang }) {
  const format = (value) => (gauge.money ? money(value, lang) : String(value));
  const left = Math.max(0, gauge.limit - gauge.used);

  return (
    <div className={`plan-gauge ${gauge.state}`}>
      <span className="plan-gauge-label">{t(LABELS[gauge.key])}</span>
      <b>
        {format(gauge.used)}
        <em>/ {format(gauge.limit)}</em>
      </b>
      <span className="meter" aria-hidden="true">
        <i className={TONES[gauge.state]} style={{ width: `${Math.min(100, gauge.ratio * 100)}%` }} />
      </span>
      <small>
        {gauge.state === "reached"
          ? t("gaugeSpent")
          : t("gaugeLeft", { left: gauge.money ? money(left, lang) : left })}
      </small>
    </div>
  );
}

/**
 * The plan, live.
 *
 * A plan that only exists in a settings card is a document; this strip puts the
 * day's usage of it next to the journal, so the limit is visible before the
 * trade that breaks it, not in the report afterwards.
 */
export default function PlanStatus({ t, lang, plan, trades = [], balance, onWritePlan }) {
  if (!plan) {
    return (
      <section className="plan-status is-empty">
        <div>
          <p className="eyebrow">{t("planTag")}</p>
          <h3>{t("planInviteTitle")}</h3>
          <p className="muted">{t("planInviteText")}</p>
        </div>
        <Button variant="secondary" className="compact" onClick={onWritePlan} chevron="→">
          {t("planWrite")}
        </Button>
      </section>
    );
  }

  const usage = planUsage(plan, trades, balance);
  const state = usage.reached.length ? "reached" : usage.gauges.some((g) => g.state === "near") ? "near" : "ok";

  const rules = [
    plan.require_stop_loss ? t("ruleStopShort") : null,
    t("planRiskLine", { limit: decimal(plan.max_risk_per_trade_pct, lang) }),
    plan.allowed_instruments?.length ? plan.allowed_instruments.join(" · ") : t("ruleAnyInstrument"),
  ].filter(Boolean);

  return (
    <section className={`plan-status ${state}`} aria-live="polite">
      <header>
        <div>
          <p className="eyebrow">{t("planTodayTag")}</p>
          <h3>{t(state === "reached" ? "planStandDown" : state === "near" ? "planNearLimit" : "planOnTrack")}</h3>
        </div>
        <span className="plan-version" title={t("planInForce")}>
          v{plan.version} · {t("planSince", { date: shortDate(plan.valid_from, lang) })}
        </span>
      </header>

      {usage.gauges.length > 0 && (
        <div className="plan-gauges">
          {usage.gauges.map((gauge) => (
            <Gauge key={gauge.key} gauge={gauge} t={t} lang={lang} />
          ))}
        </div>
      )}

      <p className="plan-rules-line">{rules.join("  ·  ")}</p>
    </section>
  );
}
