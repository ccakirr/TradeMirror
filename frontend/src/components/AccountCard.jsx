import { changePercent, money, percent, sign } from "../lib/format";
import { Skeleton } from "./ui";

export default function AccountCard({ account, summary, plan = null, t, lang, onClick }) {
  const delta = changePercent(account.initial_balance, account.current_balance);
  const tradeLabel =
    summary === undefined
      ? null
      : summary.total === 1
        ? t("tradeCountOne")
        : t("tradeCount", { count: summary.total });

  return (
    <button type="button" className="account-card" onClick={onClick}>
      <div className="account-card-top">
        <span className="account-symbol" aria-hidden="true">
          ↗
        </span>
        <span className="active-dot">{t("active")}</span>
      </div>

      <h3>{account.name}</h3>
      <span className="account-number">
        {String(account.id).slice(0, 8)} · {t("personal")}
      </span>

      <div className="account-balance">
        <span>{t("current")}</span>
        <strong>{money(account.current_balance, lang)}</strong>
        <small className={sign(delta)}>
          {percent(delta, lang)} · {t("initial")} {money(account.initial_balance, lang)}
        </small>
      </div>

      <div className="account-card-foot">
        {tradeLabel === null ? (
          <Skeleton width={70} height={10} />
        ) : (
          <span>
            {tradeLabel}
            {summary.open > 0 && <em className="open-pill">{summary.open} {t("openLabel")}</em>}
            {/* An account without rules is the one worth spotting from here. */}
            <em className={`plan-pill ${plan ? plan.state : "none"}`}>
              {plan ? `v${plan.version}` : t("noPlanShort")}
            </em>
          </span>
        )}
        <b>{t("open")} →</b>
      </div>
    </button>
  );
}
