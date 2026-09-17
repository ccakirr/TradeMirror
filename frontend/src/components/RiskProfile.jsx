import { useEffect, useState } from "react";
import { Button, Field } from "./ui";

const EMPTY = {
  instrument: "crypto",
  risk_per_trade_pct: "1",
  trades_per_month: "20",
  avg_win_hold_days: "2",
  avg_loss_hold_days: "3",
  diversification: "4",
  follows_plan: "8",
  position_sizing_discipline: "8",
};

export default function RiskProfile({ t, profile, onSave, assessments = [], planActive = false }) {
  const [form, setForm] = useState(EMPTY);
  const [open, setOpen] = useState(!profile);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (profile) {
      setForm({ ...profile });
      setOpen(false);
    }
  }, [profile]);

  const update = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      await onSave({
        ...form,
        risk_per_trade_pct: Number(form.risk_per_trade_pct),
        trades_per_month: Number(form.trades_per_month),
        avg_win_hold_days: Number(form.avg_win_hold_days),
        avg_loss_hold_days: Number(form.avg_loss_hold_days),
        diversification: Number(form.diversification),
        follows_plan: Number(form.follows_plan),
        position_sizing_discipline: Number(form.position_sizing_discipline),
      });
      setOpen(false);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setPending(false);
    }
  };

  return (
    <section className="risk-profile card">
      <div className="card-title">
        <div>
          <p className="eyebrow">{t("riskProfileTag")}</p>
          <h2>{t("riskProfileTitle")}</h2>
        </div>
        <Button variant="ghost" className="compact" onClick={() => setOpen((value) => !value)}>
          {open ? t("cancel") : t("edit")}
        </Button>
      </div>

      {open ? (
        <form className="risk-profile-form" onSubmit={submit}>
          <p className="muted">{t("riskProfileText")}</p>
          <div className="risk-profile-fields">
            <Field label={t("profileInstrument")}>
              <select value={form.instrument} onChange={update("instrument")}>
                {[
                  ["crypto", "Crypto"], ["forex", "Forex"], ["stocks", "Stocks"],
                  ["futures", "Futures"], ["options", "Options"], ["etf", "ETF"],
                ].map(([value, label]) => <option value={value} key={value}>{label}</option>)}
              </select>
            </Field>
            {[
              ["risk_per_trade_pct", "riskPerTrade"], ["trades_per_month", "tradesPerMonth"],
              ["avg_win_hold_days", "avgWinHold"], ["avg_loss_hold_days", "avgLossHold"],
              ["diversification", "diversification"], ["follows_plan", "followsPlan"],
              ["position_sizing_discipline", "positionSizing"],
            ].map(([key, label]) => (
              <Field label={t(label)} key={key}>
                <input type="number" min="0" max={key.includes("plan") || key === "position_sizing_discipline" ? "10" : undefined} step="any" value={form[key]} onChange={update(key)} />
              </Field>
            ))}
          </div>
          <Button type="submit" variant="primary" pending={pending}>{pending ? t("saving") : t("saveProfile")}</Button>
          {error && <p className="form-message" role="alert">{error}</p>}
        </form>
      ) : (
        <div className="risk-profile-summary">
          <span>{t("profileInstrument")}: <b>{profile?.instrument || "—"}</b></span>
          <span>{t("riskPerTrade")}: <b>{profile?.risk_per_trade_pct ?? "—"}%</b></span>
          <span>{t("tradesPerMonth")}: <b>{profile?.trades_per_month ?? "—"}</b></span>
          <span>{t("assessments")}: <b>{assessments.length}</b></span>
          {planActive && <p className="behavior-note">{t("profileVsPlan")}</p>}
        </div>
      )}
    </section>
  );
}
