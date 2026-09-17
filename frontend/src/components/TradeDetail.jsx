import { useEffect, useRef, useState } from "react";
import { dateTime, decimal, duration, money, percent, price, sign, signedMoney } from "../lib/format";
import {
  exitVerdict,
  holdingMs,
  notional,
  rMultiple,
  riskAmount,
  riskReward,
  tradeReturnPercent,
} from "../lib/trades";
import { quantize, stepDecimals } from "../lib/instruments";
import { findingText, VERDICT_KEYS as RISK_VERDICT_KEYS } from "../lib/riskReport";
import { Badge, Button, Spinner } from "./ui";

const VERDICT_KEYS = { target: "exitTarget", stop: "exitStop", manual: "exitManual" };

function Row({ label, value, tone }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd className={tone}>{value ?? "—"}</dd>
    </div>
  );
}

/**
 * The trade lifecycle in one panel: what was planned, what was executed, how it
 * ended — and the risk report that reads those three against each other.
 */
export default function TradeDetail({
  t,
  lang,
  trade,
  instrument,
  plan = null,
  onLoad,
  onCloseTrade,
  assessments = [],
  onLoadAssessments,
  report = null,
  onLoadReport,
  onDismiss,
}) {
  const [refreshing, setRefreshing] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);
  const [reportFailed, setReportFailed] = useState(false);
  const [closing, setClosing] = useState(false);
  const [exitPrice, setExitPrice] = useState("");
  const [closeError, setCloseError] = useState("");
  const [pending, setPending] = useState(false);
  const exitRef = useRef(null);
  const panelRef = useRef(null);
  const loadRef = useRef(onLoad);
  const loadAssessmentsRef = useRef(onLoadAssessments);
  const loadReportRef = useRef(onLoadReport);

  useEffect(() => {
    loadRef.current = onLoad;
    loadAssessmentsRef.current = onLoadAssessments;
    loadReportRef.current = onLoadReport;
  });

  // The list already holds a copy, so the panel paints instantly and then
  // reconciles with the server.
  useEffect(() => {
    let cancelled = false;
    setLoadFailed(false);
    setRefreshing(true);

    loadRef
      .current(trade.id)
      .catch(() => {
        if (!cancelled) setLoadFailed(true);
      })
      .finally(() => {
        if (!cancelled) setRefreshing(false);
      });

    return () => {
      cancelled = true;
    };
  }, [trade.id]);

  useEffect(() => {
    loadAssessmentsRef.current?.(trade.id).catch(() => {});
  }, [trade.id]);

  // The report is derived on demand, so every open asks for a fresh one — a
  // trade closed a second ago must not be judged on its entry alone.
  useEffect(() => {
    let cancelled = false;
    setReportFailed(false);

    loadReportRef.current?.(trade.id).catch(() => {
      if (!cancelled) setReportFailed(true);
    });

    return () => {
      cancelled = true;
    };
  }, [trade.id, trade.is_closed]);

  // A different trade is a different panel: never carry a half-typed exit over.
  useEffect(() => {
    setClosing(false);
    setExitPrice("");
    setCloseError("");
    panelRef.current?.focus();
  }, [trade.id]);

  useEffect(() => {
    if (closing) exitRef.current?.focus();
  }, [closing]);

  // Escape backs out one level at a time: the close form first, then the panel.
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key !== "Escape") return;
      if (closing) {
        setClosing(false);
        setExitPrice("");
        setCloseError("");
      } else {
        onDismiss();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [closing, onDismiss]);

  const submitClose = async (event) => {
    event.preventDefault();
    if (!(Number(exitPrice) > 0)) {
      setCloseError(t("exitRequired"));
      return;
    }
    setPending(true);
    try {
      // Same rule as the entry: the exit must sit on the instrument's increment.
      await onCloseTrade(trade, priceStep ? quantize(exitPrice, priceStep) : exitPrice);
      setClosing(false);
      setExitPrice("");
      setCloseError("");
    } catch (error) {
      setCloseError(error.message);
    } finally {
      setPending(false);
    }
  };

  const priceStep = instrument?.price_step || null;
  const closed = trade.is_closed;
  const returned = tradeReturnPercent(trade);
  const ratio = riskReward(trade);
  const risk = riskAmount(trade);
  const value = notional(trade);
  const r = rMultiple(trade);
  const held = holdingMs(trade);
  const verdict = exitVerdict(trade);
  const hasPlan = Boolean(trade.stop_loss || trade.take_profit);

  return (
    <aside
      className="card trade-detail"
      id="trade-detail-panel"
      ref={panelRef}
      tabIndex={-1}
      aria-label={`${t("tradeDetail")} — ${trade.instrument}`}
    >
      <header className="trade-detail-head">
        <div>
          <p className="eyebrow">{t("tradeDetail")}</p>
          <h2>{trade.instrument}</h2>
          <div className="trade-detail-tags">
            <Badge tone={trade.is_long ? "long" : "short"}>{trade.is_long ? t("long") : t("short")}</Badge>
            <span className={closed ? "closed-label" : "trade-live"}>{closed ? t("closedLabel") : t("openLabel")}</span>
            {refreshing && <Spinner label={t("loading")} />}
          </div>
        </div>
        <button type="button" className="panel-close" onClick={onDismiss} aria-label={t("closeDetail")}>
          ×
        </button>
      </header>

      <div className="trade-detail-result">
        {closed ? (
          <>
            <strong className={sign(trade.pnl)}>{signedMoney(trade.pnl, lang)}</strong>
            {returned !== null && <small className={sign(returned)}>{percent(returned, lang)}</small>}
          </>
        ) : (
          <>
            <strong className="flat">{t("stillOpen")}</strong>
            <small>
              {t("openedAt")} · {dateTime(trade.opened_at, lang)}
            </small>
          </>
        )}
      </div>

      {loadFailed && (
        <p className="panel-warning" role="status">
          {t("detailFailed")}
        </p>
      )}

      <section className="trade-detail-block">
        <p className="eyebrow">{t("plan")}</p>
        {/* The account's rules as they stood when this was opened — a plan
            published since does not get to re-judge an old trade. */}
        {plan && (
          <p className="trade-plan-line">
            <b>v{plan.version}</b>
            <span>{t("openedUnderPlan")}</span>
            <em>{t("planRiskLine", { limit: decimal(plan.max_risk_per_trade_pct, lang) })}</em>
          </p>
        )}
        {hasPlan ? (
          <dl className="trade-details">
            <Row label={t("stop")} value={trade.stop_loss ? price(trade.stop_loss, lang) : null} />
            <Row label={t("target")} value={trade.take_profit ? price(trade.take_profit, lang) : null} />
            <Row label={t("riskReward")} value={ratio ? `${decimal(ratio, lang)} : 1` : null} />
            <Row label={t("riskAtStop")} value={risk === null ? null : money(risk, lang)} />
          </dl>
        ) : (
          <p className="panel-note">{t("noPlanRecorded")}</p>
        )}
      </section>

      <section className="trade-detail-block">
        <p className="eyebrow">{t("execution")}</p>
        <dl className="trade-details">
          <Row label={t("entry")} value={price(trade.entry_price, lang)} />
          <Row label={t("exit")} value={trade.exit_price ? price(trade.exit_price, lang) : null} />
          <Row label={t("position")} value={price(trade.position_size, lang)} />
          <Row label={t("positionValue")} value={value === null ? null : money(value, lang)} />
          <Row
            label={t("openedAt")}
            value={<time dateTime={trade.opened_at}>{dateTime(trade.opened_at, lang)}</time>}
          />
          <Row
            label={t("closedAt")}
            value={trade.closed_at ? <time dateTime={trade.closed_at}>{dateTime(trade.closed_at, lang)}</time> : null}
          />
        </dl>
      </section>

      {closed && (
        <section className="trade-detail-block">
          <p className="eyebrow">{t("outcome")}</p>
          <dl className="trade-details">
            <Row
              label={t("rMultiple")}
              value={r === null ? null : `${r > 0 ? "+" : ""}${decimal(r, lang)}R`}
              tone={r === null ? undefined : sign(r)}
            />
            <Row label={t("exitType")} value={verdict ? t(VERDICT_KEYS[verdict]) : null} />
            <Row label={t("heldFor")} value={held === null ? null : duration(held, lang)} />
          </dl>
        </section>
      )}

      <section className="trade-detail-block">
        <p className="eyebrow">{t("riskReport")}</p>
        {report ? (
          <div className="risk-report">
            <div className="risk-report-verdict">
              <b className={`risk-${report.risk_class}`}>{t(RISK_VERDICT_KEYS[report.risk_class])}</b>
              <small>
                {report.score == null
                  ? t("modelNoScore")
                  : `${t("modelScore")} ${decimal(report.score, lang, 3)}`}
              </small>
            </div>

            {/* The plan block above already shows the risk in currency; here it
                only matters next to the account it was taken on. */}
            <dl className="trade-details">
              <Row
                label={t("riskOfBalance")}
                value={report.risk_pct == null ? null : `${decimal(report.risk_pct, lang)}%`}
              />
              <Row label={t("planLimit")} value={`${decimal(report.risk_limit_pct, lang)}%`} />
              <Row label={t("exposure")} value={`${decimal(report.exposure_pct, lang)}%`} />
            </dl>

            <ul className="risk-findings">
              {report.findings.map((finding) => (
                <li key={finding.code} className={`finding-${finding.level}`}>
                  <span aria-hidden="true" />
                  <p>{findingText(t, lang, finding)}</p>
                </li>
              ))}
            </ul>

            {assessments.length > 0 && (
              <div className="risk-assessment-list">
                {assessments.map((assessment) => (
                  <div className="risk-assessment" key={assessment.id}>
                    <span>{assessment.stage === "entry" ? t("entryRisk") : t("exitRisk")}</span>
                    <b className={`risk-${assessment.risk_class}`}>{assessment.risk_class.toUpperCase()}</b>
                    <small>{decimal(assessment.score, lang, 3)}</small>
                  </div>
                ))}
              </div>
            )}

            <p className="risk-report-note">{t("riskReportNote")}</p>
          </div>
        ) : (
          <p className="panel-note">{reportFailed ? t("riskReportFailed") : t("loading")}</p>
        )}
      </section>

      <section className="trade-detail-block">
        <p className="eyebrow">{t("notes")}</p>
        {trade.notes ? <p className="trade-detail-notes">{trade.notes}</p> : <p className="panel-note">{t("noNotes")}</p>}
      </section>

      {!closed &&
        (closing ? (
          <form className="close-form" onSubmit={submitClose}>
            <label>
              <span className="sr-only">{t("exit")}</span>
              <input
                ref={exitRef}
                type="number"
                min={priceStep || "0.0001"}
                step={priceStep || "any"}
                inputMode="decimal"
                placeholder={t("exit")}
                value={exitPrice}
                onChange={(event) => {
                  setExitPrice(event.target.value);
                  if (closeError) setCloseError("");
                }}
                onBlur={() => priceStep && setExitPrice((current) => quantize(current, priceStep))}
                aria-invalid={closeError ? "true" : undefined}
              />
            </label>
            {priceStep && (
              <span className="close-hint">
                {t("stepHint", { step: decimal(priceStep, lang, stepDecimals(priceStep)) })}
              </span>
            )}
            <Button type="submit" variant="primary" className="compact" pending={pending}>
              {pending ? t("saving") : t("save")}
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="compact"
              disabled={pending}
              onClick={() => {
                setClosing(false);
                setExitPrice("");
                setCloseError("");
              }}
            >
              {t("cancel")}
            </Button>
            {closeError && (
              <span className="close-error" role="alert">
                {closeError}
              </span>
            )}
          </form>
        ) : (
          <Button variant="secondary" className="compact" onClick={() => setClosing(true)}>
            {t("closePosition")}
          </Button>
        ))}
    </aside>
  );
}
