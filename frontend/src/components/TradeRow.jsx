import { decimal, percent, price, sign, signedMoney } from "../lib/format";
import { rMultiple, tradeReturnPercent } from "../lib/trades";
import { Badge } from "./ui";

/** A journal line: summary only. Everything else lives in the detail panel. */
export default function TradeRow({ trade, t, lang, riskPct = null, limitPct, planVersion = null, selected, onSelect }) {
  const returned = tradeReturnPercent(trade);
  const r = rMultiple(trade);

  // The risk is the part worth seeing while scanning: a run of trades without a
  // stop, or every one of them over the limit, is the pattern this journal is for.
  const riskTone =
    riskPct === null || !limitPct ? "" : riskPct > limitPct * 2 ? "bad" : riskPct > limitPct ? "warn" : "good";

  return (
    <li className={`trade ${trade.is_closed ? "is-closed" : "is-open"} ${selected ? "is-selected" : ""}`}>
      <button
        type="button"
        className="trade-row"
        onClick={() => onSelect(trade)}
        aria-expanded={selected}
        aria-controls="trade-detail-panel"
        aria-label={selected ? t("hideDetails") : t("showDetails")}
      >
        <Badge tone={trade.is_long ? "long" : "short"}>{trade.is_long ? t("long") : t("short")}</Badge>

        <span className="trade-main">
          <span className="trade-instrument">{trade.instrument}</span>
          <span className="trade-meta">
            {t("entry")} {price(trade.entry_price, lang)} · {price(trade.position_size, lang)}
          </span>
          <span className="trade-tags">
            {trade.stop_loss ? (
              riskPct !== null && (
                <b className={`risk-chip ${riskTone}`} title={t("riskOfBalance")}>
                  {decimal(riskPct, lang)}%
                </b>
              )
            ) : (
              <b className="risk-chip bad" title={t("previewNoStop")}>
                {t("noStopChip")}
              </b>
            )}
            {r !== null && (
              <b className={`risk-chip ${sign(r)}`} title={t("rMultiple")}>
                {r > 0 ? "+" : ""}
                {decimal(r, lang)}R
              </b>
            )}
            {/* Which version of the plan this trade was opened under — an old
                trade is judged by the rules that were in force back then. */}
            {planVersion !== null && (
              <b className="risk-chip plan" title={t("planInForce")}>
                v{planVersion}
              </b>
            )}
          </span>
        </span>

        <span className="trade-result">
          {trade.is_closed ? (
            <>
              <b className={sign(trade.pnl)}>{signedMoney(trade.pnl, lang)}</b>
              {returned !== null && <small className={sign(returned)}>{percent(returned, lang)}</small>}
            </>
          ) : (
            <span className="trade-live">{t("openLabel")}</span>
          )}
        </span>

        <span className="trade-chevron" aria-hidden="true">
          {selected ? "▾" : "›"}
        </span>
      </button>
    </li>
  );
}
