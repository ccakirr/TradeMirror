import { useEffect, useMemo, useState } from "react";
import { decimal, shortDate } from "../lib/format";
import { activePlan, planDiff, RULES } from "../lib/plan";
import { Button, EmptyState, Field, Toggle } from "./ui";
import TagInput from "./TagInput";

const BLANK = {
  max_risk_per_trade_pct: "1",
  max_daily_loss_pct: "3",
  max_trades_per_day: "",
  max_open_positions: "",
  require_stop_loss: true,
  allowed_instruments: [],
  allowed_setups: [],
};

/** A rule as a sentence rather than a raw column value. */
function ruleValue(rule, value, t, lang) {
  if (rule.kind === "pct") return `${decimal(value, lang)}%`;
  if (rule.kind === "count") return value ? String(value) : t("ruleNoLimit");
  if (rule.kind === "bool") return value ? t("ruleRequired") : t("ruleOptional");
  return value?.length ? value.join(", ") : t("ruleAny");
}

/** An amended version reads as a change, so both sides of it are shown. */
function Change({ change, t, lang }) {
  return (
    <li>
      <span>{t(change.label)}</span>
      <b>
        <s>{ruleValue(change, change.from, t, lang)}</s> → {ruleValue(change, change.to, t, lang)}
      </b>
    </li>
  );
}

/**
 * The rules the account trades by, and how they got there.
 *
 * Saving never overwrites: it publishes a new version and closes the current
 * one, so a trade from last month is still judged by the plan that was in force
 * when it was opened.
 */
export default function TradingPlan({ t, lang, plans = [], instruments = [], open, setOpen, onCreate }) {
  const plan = activePlan(plans);
  const [form, setForm] = useState(BLANK);
  const [pending, setPending] = useState(false);
  const [errors, setErrors] = useState({});
  const [showHistory, setShowHistory] = useState(false);

  // A new version starts from the one in force — amending rules is the common
  // case, rewriting them from nothing is not.
  useEffect(() => {
    if (!open) return;
    setErrors({});
    setForm(
      plan
        ? {
            max_risk_per_trade_pct: String(plan.max_risk_per_trade_pct ?? ""),
            max_daily_loss_pct: String(plan.max_daily_loss_pct ?? ""),
            max_trades_per_day: plan.max_trades_per_day ? String(plan.max_trades_per_day) : "",
            max_open_positions: plan.max_open_positions ? String(plan.max_open_positions) : "",
            require_stop_loss: Boolean(plan.require_stop_loss),
            allowed_instruments: [...(plan.allowed_instruments || [])],
            allowed_setups: [...(plan.allowed_setups || [])],
          }
        : BLANK,
    );
  }, [open, plan]);

  const options = useMemo(
    () => instruments.map((item) => ({ value: item.symbol, label: item.name })),
    [instruments],
  );

  const update = (key) => (event) => {
    setForm((current) => ({ ...current, [key]: event.target.value }));
    if (errors[key]) setErrors((current) => ({ ...current, [key]: "" }));
  };

  const submit = async (event) => {
    event.preventDefault();

    const next = {};
    if (!(Number(form.max_risk_per_trade_pct) > 0)) next.max_risk_per_trade_pct = t("ruleAboveZero");
    if (!(Number(form.max_daily_loss_pct) > 0)) next.max_daily_loss_pct = t("ruleAboveZero");
    setErrors(next);
    if (Object.keys(next).length) return;

    const count = (raw) => (Number(raw) > 0 ? Math.round(Number(raw)) : null);

    setPending(true);
    try {
      await onCreate({
        max_risk_per_trade_pct: Number(form.max_risk_per_trade_pct),
        max_daily_loss_pct: Number(form.max_daily_loss_pct),
        max_trades_per_day: count(form.max_trades_per_day),
        max_open_positions: count(form.max_open_positions),
        require_stop_loss: form.require_stop_loss,
        allowed_instruments: form.allowed_instruments,
        allowed_setups: form.allowed_setups,
      });
      setOpen(false);
    } catch (reason) {
      setErrors({ form: reason.message });
    } finally {
      setPending(false);
    }
  };

  return (
    <section className="card trading-plan" id="trading-plan">
      <div className="card-title">
        <div>
          <p className="eyebrow">{t("planTag")}</p>
          <h2>{t("planTitle")}</h2>
        </div>
        {(plan || open) && (
          <Button variant={open ? "ghost" : "secondary"} className="compact" onClick={() => setOpen(!open)}>
            {open ? t("cancel") : t("planNewVersion")}
          </Button>
        )}
      </div>

      {open ? (
        <form className="plan-form" onSubmit={submit} noValidate>
          <p className="muted">{plan ? t("planAmendText", { version: plan.version }) : t("planFirstText")}</p>

          <div className="plan-fields">
            <Field
              label={t("ruleRisk")}
              error={errors.max_risk_per_trade_pct}
              hint={t("ruleRiskHint")}
              affix={<span className="affix">%</span>}
            >
              <input
                type="number"
                min="0"
                step="0.1"
                inputMode="decimal"
                value={form.max_risk_per_trade_pct}
                onChange={update("max_risk_per_trade_pct")}
              />
            </Field>

            <Field
              label={t("ruleDailyLoss")}
              error={errors.max_daily_loss_pct}
              hint={t("ruleDailyLossHint")}
              affix={<span className="affix">%</span>}
            >
              <input
                type="number"
                min="0"
                step="0.1"
                inputMode="decimal"
                value={form.max_daily_loss_pct}
                onChange={update("max_daily_loss_pct")}
              />
            </Field>

            <Field label={t("ruleTradesPerDay")} optional={t("ruleNoLimitShort")} hint={t("ruleTradesHint")}>
              <input
                type="number"
                min="1"
                step="1"
                inputMode="numeric"
                value={form.max_trades_per_day}
                onChange={update("max_trades_per_day")}
              />
            </Field>

            <Field label={t("ruleOpenPositions")} optional={t("ruleNoLimitShort")} hint={t("rulePositionsHint")}>
              <input
                type="number"
                min="1"
                step="1"
                inputMode="numeric"
                value={form.max_open_positions}
                onChange={update("max_open_positions")}
              />
            </Field>
          </div>

          <Toggle
            label={t("ruleStop")}
            hint={t("ruleStopHint")}
            checked={form.require_stop_loss}
            onChange={(checked) => setForm((current) => ({ ...current, require_stop_loss: checked }))}
          />

          <div className="plan-lists">
            <TagInput
              label={t("ruleInstruments")}
              optional={t("optional")}
              placeholder={t("ruleInstrumentsPlaceholder")}
              emptyLabel={t("ruleAnyInstrumentHint")}
              hint={t("ruleInstrumentsHint")}
              removeLabel={t("remove")}
              addLabel={t("add")}
              suggestions={options}
              value={form.allowed_instruments}
              onChange={(value) => setForm((current) => ({ ...current, allowed_instruments: value }))}
            />
            <TagInput
              free
              label={t("ruleSetups")}
              optional={t("optional")}
              placeholder={t("ruleSetupsPlaceholder")}
              emptyLabel={t("ruleAnySetupHint")}
              hint={t("ruleSetupsHint")}
              removeLabel={t("remove")}
              addLabel={t("add")}
              value={form.allowed_setups}
              onChange={(value) => setForm((current) => ({ ...current, allowed_setups: value }))}
            />
          </div>

          <Button type="submit" variant="primary" pending={pending} chevron="→">
            {pending ? t("saving") : plan ? t("planPublish") : t("planCommit")}
          </Button>

          <p className="plan-note">{t("planVersionNote")}</p>

          {errors.form && (
            <p className="form-message" role="alert">
              {errors.form}
            </p>
          )}
        </form>
      ) : plan ? (
        <>
          <dl className="plan-rules">
            {RULES.map((rule) => (
              <div key={rule.field}>
                <dt>{t(rule.label)}</dt>
                <dd className={rule.kind === "list" && !plan[rule.field]?.length ? "faint" : ""}>
                  {ruleValue(rule, plan[rule.field], t, lang)}
                </dd>
              </div>
            ))}
          </dl>

          <button
            type="button"
            className="plan-history-toggle"
            onClick={() => setShowHistory((value) => !value)}
            aria-expanded={showHistory}
          >
            {t("planHistory", { count: plans.length })}
            <span aria-hidden="true">{showHistory ? "▾" : "›"}</span>
          </button>

          {showHistory && (
            <ol className="plan-history">
              {plans.map((version, index) => {
                const previous = plans[index + 1] || null;
                const changes = planDiff(version, previous);
                return (
                  <li key={version.id} className={version.valid_to ? "" : "active"}>
                    <div className="plan-history-head">
                      <b>v{version.version}</b>
                      <span>
                        {shortDate(version.valid_from, lang)} —{" "}
                        {version.valid_to ? shortDate(version.valid_to, lang) : t("now")}
                      </span>
                      {!version.valid_to && <em>{t("planActive")}</em>}
                    </div>
                    {previous ? (
                      <ul className="plan-history-changes">
                        {changes.length ? (
                          changes.map((change) => (
                            <Change key={change.field} change={change} t={t} lang={lang} />
                          ))
                        ) : (
                          <li className="faint">{t("planNoChange")}</li>
                        )}
                      </ul>
                    ) : (
                      <p className="plan-history-first">{t("planFirstVersion")}</p>
                    )}
                  </li>
                );
              })}
            </ol>
          )}
        </>
      ) : (
        <EmptyState
          icon="◇"
          title={t("planEmptyTitle")}
          text={t("planEmptyText")}
          action={
            <Button variant="primary" className="compact" chevron="→" onClick={() => setOpen(true)}>
              {t("planWrite")}
            </Button>
          }
        />
      )}
    </section>
  );
}
