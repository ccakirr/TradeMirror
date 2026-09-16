import { decimal } from "../lib/format";

/** A share of something, drawn so a glance is enough. */
function Meter({ value, tone }) {
  return (
    <span className="meter" aria-hidden="true">
      <i className={tone} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </span>
  );
}

function Line({ label, value, hint, tone = "", meter }) {
  return (
    <div className="behavior-line">
      <span>{label}</span>
      <b className={tone}>{value}</b>
      {meter !== undefined && <Meter value={meter} tone={tone} />}
      {hint && <small>{hint}</small>}
    </div>
  );
}

/**
 * What the journal says about the habit, not the trade: how often a stop was
 * set, how often the exit honored the plan, and what the risk actually was.
 * A metric without data stays empty — missing history is never counted as zero.
 */
export default function BehaviorPanel({ t, lang, behavior, limitPct, hasProfile }) {
  const share = (value) => (value === null ? "—" : `${Math.round(value)}%`);
  const shareTone = (value, good, fair) =>
    value === null ? "" : value >= good ? "positive" : value >= fair ? "caution" : "negative";

  const riskTone =
    behavior.avgRisk === null || !limitPct
      ? ""
      : behavior.avgRisk > limitPct * 2
        ? "negative"
        : behavior.avgRisk > limitPct
          ? "caution"
          : "positive";

  return (
    <section className="card insight">
      <p className="eyebrow">{t("insight")}</p>
      <h2>{t("riskPicture")}</h2>

      {behavior.total ? (
        <>
          <p className="muted">{t("behaviorText")}</p>

          <Line
            label={t("stopUsage")}
            value={share(behavior.stopUsage)}
            tone={shareTone(behavior.stopUsage, 90, 60)}
            meter={behavior.stopUsage ?? 0}
            hint={behavior.missingStops ? t("missingStops", { count: behavior.missingStops }) : undefined}
          />

          <Line
            label={t("planAdherence")}
            value={share(behavior.adherence)}
            tone={shareTone(behavior.adherence, 70, 40)}
            meter={behavior.adherence ?? 0}
            hint={behavior.plannedCount ? t("ofPlanned", { count: behavior.plannedCount }) : t("notEnough")}
          />

          <Line
            label={t("avgRisk")}
            value={behavior.avgRisk === null ? "—" : `${decimal(behavior.avgRisk, lang)}%`}
            tone={riskTone}
            hint={
              behavior.breaches
                ? t("breachCount", { count: behavior.breaches })
                : limitPct
                  ? `${t("planLimit")} ${decimal(limitPct, lang)}%`
                  : undefined
            }
          />

          <Line
            label={t("avgRewardRisk")}
            value={behavior.avgReward === null ? "—" : `${decimal(behavior.avgReward, lang)} : 1`}
            tone={behavior.avgReward === null ? "" : behavior.avgReward >= 2 ? "positive" : "caution"}
          />

          <Line
            label={t("avgOutcome")}
            value={
              behavior.avgR === null
                ? "—"
                : `${behavior.avgR > 0 ? "+" : ""}${decimal(behavior.avgR, lang)}R`
            }
            tone={
              behavior.avgR === null || behavior.avgR === 0
                ? ""
                : behavior.avgR > 0
                  ? "positive"
                  : "negative"
            }
            hint={behavior.closed ? t("closedCount", { count: behavior.closed }) : t("notEnough")}
          />

          {!hasProfile && <p className="behavior-note">{t("defaultLimitNote", { limit: decimal(limitPct, lang) })}</p>}
        </>
      ) : (
        <p className="muted">{t("behaviorEmpty")}</p>
      )}
    </section>
  );
}
