import { useEffect, useMemo, useRef, useState } from "react";
import { changePercent, decimal, fullDate, money, percent, sign, signedMoney } from "../lib/format";
import { summarize } from "../lib/trades";
import { CATEGORY_KEYS, quantize, stepDecimals } from "../lib/instruments";
import { Button, EmptyState, Field, Segmented, Skeleton } from "./ui";
import Combobox from "./Combobox";
import { Stat, StatGrid } from "./Stats";
import TradeRow from "./TradeRow";
import TradeDetail from "./TradeDetail";
import RiskProfile from "./RiskProfile";

const emptyTrade = {
  instrument: "",
  is_long: true,
  entry_price: "",
  position_size: "",
  stop_loss: "",
  take_profit: "",
  notes: "",
};

export default function AccountDetail({
  t,
  lang,
  account,
  trades,
  loading,
  instruments = [],
  back,
  onCreateTrade,
  onCloseTrade,
  onLoadTrade,
  riskProfile,
  onSaveRiskProfile,
  riskAssessmentsByTrade = {},
  onLoadRiskAssessments,
}) {
  const [form, setForm] = useState(emptyTrade);
  const [errors, setErrors] = useState({});
  const [pending, setPending] = useState(false);
  const [filter, setFilter] = useState("all");
  const [formOpen, setFormOpen] = useState(false);
  const [selectedTradeId, setSelectedTradeId] = useState(null);
  const instrumentRef = useRef(null);

  const list = trades || [];
  const summary = useMemo(() => summarize(list), [list]);
  const delta = changePercent(account.initial_balance, account.current_balance);

  // With no history the form is the point of the page; once there is a journal, the list is.
  useEffect(() => {
    if (!loading && list.length === 0) setFormOpen(true);
  }, [loading, list.length]);

  useEffect(() => {
    if (formOpen) instrumentRef.current?.focus();
  }, [formOpen]);

  // Every number on this form is shaped by the instrument, so nothing is
  // editable until one is picked from the catalog.
  const instrument = useMemo(
    () => instruments.find((item) => item.symbol === form.instrument) || null,
    [instruments, form.instrument],
  );

  const options = useMemo(
    () =>
      instruments.map((item) => ({
        value: item.symbol,
        label: item.name,
        tag: item.venue,
      })),
    [instruments, t],
  );

  const priceStep = instrument?.price_step || null;
  const sizeStep = instrument?.size_step || null;

  const stepHint = (step) =>
    step ? t("stepHint", { step: decimal(step, lang, stepDecimals(step)) }) : undefined;

  // Round to the instrument's increment as soon as the field is left, so the
  // value on screen is the value the API will store.
  const snap = (key, step) => () => {
    if (!step) return;
    setForm((current) => {
      const next = quantize(current[key], step);
      return next === current[key] ? current : { ...current, [key]: next };
    });
  };

  const selectedTrade = useMemo(
    () => list.find((trade) => trade.id === selectedTradeId) || null,
    [list, selectedTradeId],
  );

  const selectedAssessments = selectedTrade ? riskAssessmentsByTrade[selectedTrade.id] || [] : [];

  const selectedInstrument = useMemo(
    () => (selectedTrade ? instruments.find((item) => item.symbol === selectedTrade.instrument) || null : null),
    [instruments, selectedTrade],
  );

  // Switching accounts must not leave another journal's trade open.
  useEffect(() => {
    setSelectedTradeId(null);
  }, [account.id]);

  const visible = useMemo(() => {
    if (filter === "open") return list.filter((trade) => !trade.is_closed);
    if (filter === "closed") return list.filter((trade) => trade.is_closed);
    return list;
  }, [list, filter]);

  const update = (key) => (event) => {
    const value = key === "is_long" ? event.target.value === "true" : event.target.value;
    setForm((current) => ({ ...current, [key]: value }));
    if (errors[key]) setErrors((current) => ({ ...current, [key]: "" }));
  };

  const submit = async (event) => {
    event.preventDefault();
    const next = {};
    if (!instrument) next.instrument = t("instrumentRequired");
    if (!(Number(form.entry_price) > 0)) next.entry_price = t("required");
    if (!(Number(form.position_size) > 0)) next.position_size = t("required");
    setErrors(next);
    if (Object.keys(next).length) return;

    // Submitting with a field still focused skips its blur, so quantize here too.
    // Prices travel as strings: a decimal string survives the trip exactly.
    const optional = (raw, step) => (Number(raw) > 0 ? quantize(raw, step) : null);

    setPending(true);
    try {
      await onCreateTrade({
        instrument: instrument.symbol,
        is_long: form.is_long,
        entry_price: quantize(form.entry_price, priceStep),
        position_size: quantize(form.position_size, sizeStep),
        stop_loss: optional(form.stop_loss, priceStep),
        take_profit: optional(form.take_profit, priceStep),
        notes: form.notes.trim() || null,
      });
      setForm(emptyTrade);
      instrumentRef.current?.focus();
    } catch (error) {
      setErrors({ form: error.message });
    } finally {
      setPending(false);
    }
  };

  const emptyMessage =
    filter === "open" ? t("noOpenTrades") : filter === "closed" ? t("noClosedTrades") : t("journalStart");

  return (
    <>
      <button type="button" className="back" onClick={back}>
        <span aria-hidden="true">←</span> {t("back")}
      </button>

      <section className="detail-hero">
        <div>
          <p className="eyebrow">{t("overviewTag")}</p>
          <h2>{account.name}</h2>
          <p className="muted">
            {t("personal")} · {fullDate(account.created_at, lang)}
          </p>
        </div>
        <div className="detail-balance">
          <span>{t("current")}</span>
          <strong>{money(account.current_balance, lang)}</strong>
          <small className={sign(delta)}>
            {percent(delta, lang)} · {t("initial")} {money(account.initial_balance, lang)}
          </small>
        </div>
      </section>

      <StatGrid>
        <Stat label={t("logged")} value={summary.total} loading={loading} />
        <Stat label={t("openPositions")} value={summary.open} loading={loading} />
        <Stat
          label={t("winRate")}
          value={summary.winRate === null ? "—" : `${Math.round(summary.winRate)}%`}
          hint={summary.closed ? t("closedCount", { count: summary.closed }) : t("needsHistory")}
          loading={loading}
        />
        <Stat
          label={t("realized")}
          value={summary.closed ? signedMoney(summary.realized, lang) : "—"}
          tone={summary.closed ? sign(summary.realized) : "flat"}
          hint={t("balanceNote")}
          loading={loading}
        />
      </StatGrid>

      <div className="detail-grid">
        <section className="card journal-card">
          <div className="card-title">
            <div>
              <p className="eyebrow">{t("journal")}</p>
              <h2>{t("recent")}</h2>
            </div>
            <Button
              variant={formOpen ? "ghost" : "secondary"}
              className="compact"
              onClick={() => setFormOpen((value) => !value)}
            >
              {formOpen ? t("cancel") : `+ ${t("newTrade")}`}
            </Button>
          </div>

          {list.length > 0 && (
            <Segmented
              label={t("journal")}
              value={filter}
              onChange={setFilter}
              options={[
                { value: "all", label: t("filterAll"), count: summary.total },
                { value: "open", label: t("filterOpen"), count: summary.open },
                { value: "closed", label: t("filterClosed"), count: summary.closed },
              ]}
            />
          )}

          {loading ? (
            <ul className="trade-list">
              {[0, 1, 2].map((key) => (
                <li className="trade skeleton-row" key={key}>
                  <Skeleton width={54} height={18} radius={99} />
                  <Skeleton width="45%" height={12} />
                  <Skeleton width={70} height={12} />
                </li>
              ))}
            </ul>
          ) : visible.length ? (
            <ul className="trade-list">
              {visible.map((trade) => (
                <TradeRow
                  key={trade.id}
                  trade={trade}
                  t={t}
                  lang={lang}
                  selected={trade.id === selectedTradeId}
                  onSelect={(picked) =>
                    setSelectedTradeId((current) => (current === picked.id ? null : picked.id))
                  }
                />
              ))}
            </ul>
          ) : (
            <EmptyState
              compact
              icon={filter === "all" ? "＋" : "◷"}
              title={emptyMessage}
              text={filter === "all" ? t("journalText") : undefined}
            />
          )}

          {formOpen && (
            <form className="trade-form" onSubmit={submit} noValidate>
              <p className="eyebrow">{t("createTrade")}</p>
              <div className="trade-fields">
                <Combobox
                  label={t("instrument")}
                  placeholder={t("searchInstrument")}
                  toggleLabel={t("showInstruments")}
                  emptyText={instruments.length ? t("noInstrumentMatch") : t("catalogEmpty")}
                  options={options}
                  value={form.instrument}
                  onChange={(symbol) => {
                    setForm((current) => ({ ...current, instrument: symbol }));
                    if (errors.instrument) setErrors((current) => ({ ...current, instrument: "" }));
                  }}
                  error={errors.instrument}
                  hint={
                    instrument
                      ? `${instrument.name} · ${t(CATEGORY_KEYS[instrument.category] || "instrument")}`
                      : t("pickInstrumentFirst")
                  }
                  moreText={(count) => t("moreResults", { count })}
                  inputRef={instrumentRef}
                />
                <Field label={t("direction")}>
                  <select value={String(form.is_long)} onChange={update("is_long")}>
                    <option value="true">{t("long")}</option>
                    <option value="false">{t("short")}</option>
                  </select>
                </Field>
                <Field label={t("entry")} error={errors.entry_price} hint={stepHint(priceStep)}>
                  <input
                    type="number"
                    min={priceStep || "0.0001"}
                    step={priceStep || "any"}
                    inputMode="decimal"
                    disabled={!instrument}
                    value={form.entry_price}
                    onChange={update("entry_price")}
                    onBlur={snap("entry_price", priceStep)}
                  />
                </Field>
                <Field label={t("position")} error={errors.position_size} hint={stepHint(sizeStep)}>
                  <input
                    type="number"
                    min={sizeStep || "0.0001"}
                    step={sizeStep || "any"}
                    inputMode="decimal"
                    disabled={!instrument}
                    value={form.position_size}
                    onChange={update("position_size")}
                    onBlur={snap("position_size", sizeStep)}
                  />
                </Field>
                <Field label={t("stop")} optional={t("optional")} hint={stepHint(priceStep)}>
                  <input
                    type="number"
                    min="0"
                    step={priceStep || "any"}
                    inputMode="decimal"
                    disabled={!instrument}
                    value={form.stop_loss}
                    onChange={update("stop_loss")}
                    onBlur={snap("stop_loss", priceStep)}
                  />
                </Field>
                <Field label={t("target")} optional={t("optional")} hint={stepHint(priceStep)}>
                  <input
                    type="number"
                    min="0"
                    step={priceStep || "any"}
                    inputMode="decimal"
                    disabled={!instrument}
                    value={form.take_profit}
                    onChange={update("take_profit")}
                    onBlur={snap("take_profit", priceStep)}
                  />
                </Field>
              </div>

              <Field label={t("notes")} optional={t("optional")}>
                <textarea value={form.notes} onChange={update("notes")} rows="3" placeholder={t("notesPlaceholder")} />
              </Field>

              <Button type="submit" variant="primary" pending={pending} chevron="→">
                {pending ? t("logging") : t("logTrade")}
              </Button>

              {errors.form && (
                <p className="form-message" role="alert">
                  {errors.form}
                </p>
              )}
            </form>
          )}
        </section>

        {selectedTrade ? (
          <TradeDetail
            t={t}
            lang={lang}
            trade={selectedTrade}
            instrument={selectedInstrument}
            onLoad={onLoadTrade}
            onCloseTrade={onCloseTrade}
            assessments={selectedAssessments}
            onLoadAssessments={onLoadRiskAssessments}
            onDismiss={() => setSelectedTradeId(null)}
          />
        ) : (
          <section className="card insight">
            <p className="eyebrow">{t("insight")}</p>
            <h2>{t("riskPicture")}</h2>
            <p className="muted">{t("riskText")}</p>
            <div className="insight-line">
              <span>{t("engine")}</span>
              <b>{t("ready")}</b>
            </div>
            <div className="insight-line">
              <span>{t("history")}</span>
              <b>{summary.total || t("empty")}</b>
            </div>
            <div className="insight-line">
              <span>{t("winRate")}</span>
              <b>{summary.winRate === null ? t("empty") : `${Math.round(summary.winRate)}%`}</b>
            </div>
          </section>
        )}
      </div>

      <RiskProfile
        t={t}
        profile={riskProfile}
        assessments={selectedAssessments}
        onSave={(payload) => onSaveRiskProfile(account.id, payload)}
      />

      {/* Below the two-column breakpoint the panel is a drawer, so it needs a way out. */}
      {selectedTrade && (
        <div className="panel-scrim" onClick={() => setSelectedTradeId(null)} aria-hidden="true" />
      )}
    </>
  );
}
