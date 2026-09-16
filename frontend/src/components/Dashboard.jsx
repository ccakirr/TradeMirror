import { useMemo } from "react";
import { dateTime, money, price, sign, signedMoney } from "../lib/format";
import { summarize } from "../lib/trades";
import { Badge, Button, EmptyState, Skeleton } from "./ui";
import { Stat, StatGrid } from "./Stats";
import AccountCard from "./AccountCard";

export default function Dashboard({ t, lang, user, accounts, tradesByAccount, loading, go, open }) {
  const allTrades = useMemo(
    () =>
      accounts.flatMap((account) =>
        (tradesByAccount[account.id] || []).map((trade) => ({ ...trade, accountName: account.name })),
      ),
    [accounts, tradesByAccount],
  );

  const summary = useMemo(() => summarize(allTrades), [allTrades]);
  const total = useMemo(
    () => accounts.reduce((sum, account) => sum + Number(account.current_balance || 0), 0),
    [accounts],
  );
  const recent = useMemo(
    () => [...allTrades].sort((a, b) => new Date(b.opened_at) - new Date(a.opened_at)).slice(0, 5),
    [allTrades],
  );

  return (
    <>
      <section className="welcome">
        <div>
          <p className="eyebrow">{t("workspace")}</p>
          <h2>{t("dashboard")}</h2>
          <p>{t("greeting", { name: user.email.split("@")[0] })}</p>
        </div>
        <Button variant="primary" chevron="＋" onClick={() => go("accounts")}>
          {t("createAccount")}
        </Button>
      </section>

      <StatGrid>
        <Stat label={t("accounts")} value={accounts.length} loading={loading} />
        <Stat label={t("tracked")} value={money(total, lang)} loading={loading} />
        <Stat
          label={t("logged")}
          value={summary.total}
          hint={summary.open ? `${summary.open} ${t("openLabel")}` : t("noneOpen")}
          loading={loading}
        />
        <Stat
          label={t("realized")}
          value={summary.closed ? signedMoney(summary.realized, lang) : "—"}
          tone={summary.closed ? sign(summary.realized) : "flat"}
          hint={
            summary.winRate === null
              ? t("needsHistory")
              : `${t("winRate")} ${Math.round(summary.winRate)}%`
          }
          loading={loading}
        />
      </StatGrid>

      <section className="section-head">
        <div>
          <p className="eyebrow">{t("yourAccounts")}</p>
          <h2>{t("chooseSpace")}</h2>
        </div>
        {accounts.length > 3 && (
          <button type="button" className="text-button" onClick={() => go("accounts")}>
            {t("viewAll")} <b aria-hidden="true">→</b>
          </button>
        )}
      </section>

      {loading && !accounts.length ? (
        <div className="account-grid">
          {[0, 1, 2].map((key) => (
            <div className="account-card skeleton-card" key={key}>
              <Skeleton width={31} height={31} radius={99} />
              <Skeleton width="70%" height={19} />
              <Skeleton width="40%" height={10} />
              <Skeleton width="55%" height={25} />
            </div>
          ))}
        </div>
      ) : accounts.length ? (
        <div className="account-grid">
          {accounts.slice(0, 3).map((account) => (
            <AccountCard
              key={account.id}
              account={account}
              summary={tradesByAccount[account.id] ? summarize(tradesByAccount[account.id]) : undefined}
              t={t}
              lang={lang}
              onClick={() => open(account)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title={t("noAccounts")}
          text={t("structureText")}
          action={
            <Button variant="secondary" chevron="→" onClick={() => go("accounts")}>
              {t("firstAccount")}
            </Button>
          }
        />
      )}

      <section className="section-head">
        <div>
          <p className="eyebrow">{t("acrossAccounts")}</p>
          <h2>{t("recentActivity")}</h2>
        </div>
      </section>

      <section className="card activity-card">
        {recent.length ? (
          <ul className="activity-list">
            {recent.map((trade) => (
              <li key={trade.id}>
                <Badge tone={trade.is_long ? "long" : "short"}>{trade.is_long ? t("long") : t("short")}</Badge>
                <span className="activity-instrument">{trade.instrument}</span>
                <span className="activity-account">{trade.accountName}</span>
                <span className="activity-entry">
                  {t("entry")} {price(trade.entry_price, lang)}
                </span>
                {trade.is_closed ? (
                  <span className={`activity-pnl ${sign(trade.pnl)}`}>{signedMoney(trade.pnl, lang)}</span>
                ) : (
                  <span className="activity-pnl open">{t("openLabel")}</span>
                )}
                <time dateTime={trade.opened_at}>{dateTime(trade.opened_at, lang)}</time>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState compact icon="◷" title={t("noActivity")} text={t("noActivityText")} />
        )}
      </section>
    </>
  );
}
