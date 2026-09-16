import { percent, price, sign, signedMoney } from "../lib/format";
import { tradeReturnPercent } from "../lib/trades";
import { Badge } from "./ui";

/** A journal line: summary only. Everything else lives in the detail panel. */
export default function TradeRow({ trade, t, lang, selected, onSelect }) {
  const returned = tradeReturnPercent(trade);

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
