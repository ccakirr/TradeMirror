"""Regenerate ``backend/app/data/instruments.json``.

Two sources, because the two kinds of venue publish very differently:

* **Binance** exposes every tradable spot pair through a public endpoint,
  including the exact tick and lot step each one trades on. That part is real
  exchange data, pulled live.
* **Broker CFDs** (XM Global, IC Markets, Pepperstone and the rest of the
  MT4/MT5 world) publish no instruments API — their contract schedules live in
  HTML tables that differ per account type. The CFD block below is therefore a
  curated list of the symbols those brokers conventionally offer, with the tick
  sizes a five-digit broker normally quotes. Treat it as a sensible default to
  adjust against a specific broker's schedule, not as any one broker's feed.

Position sizes are journaled in **units of the base asset**, not lots, because
``pnl = (exit - entry) * position_size`` is how the service settles a trade.

Run it from the repository root:

    .venv/bin/python -m backend.scripts.sync_instruments
"""

from __future__ import annotations

import json
import urllib.request
from decimal import Decimal
from pathlib import Path


EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"
ASSET_NAMES_URL = (
    "https://www.binance.com/bapi/asset/v2/public/asset/asset/get-all-asset"
)

OUTPUT = Path(__file__).resolve().parents[1] / "app" / "data" / "instruments.json"

# The trades table stores Numeric(28, 10).
MAX_DECIMALS = 10


def _plain(value: Decimal) -> str:
    """Decimal as a plain string — never 1E-8, which the clients cannot parse."""
    return format(value.normalize(), "f")


def _fetch(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "trademiror-sync"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def _filter(symbol: dict, name: str) -> dict | None:
    for entry in symbol["filters"]:
        if entry["filterType"] == name:
            return entry
    return None


def _asset_names() -> dict[str, str]:
    """Full names make the catalog searchable by "bitcoin", not just "BTC"."""
    try:
        payload = _fetch(ASSET_NAMES_URL)
    except Exception as error:  # noqa: BLE001 - the tickers alone still work
        print(f"  ! asset names unavailable ({error}); falling back to tickers")
        return {}

    names = {}
    for row in payload.get("data") or []:
        code = row.get("assetCode")
        name = row.get("assetName")
        if code and name:
            names[code] = name
    return names


def binance_instruments() -> list[dict]:
    print(f"  fetching {EXCHANGE_INFO_URL}")
    payload = _fetch(EXCHANGE_INFO_URL)
    names = _asset_names()

    instruments = []
    for symbol in payload["symbols"]:
        if symbol.get("status") != "TRADING":
            continue

        price_filter = _filter(symbol, "PRICE_FILTER")
        lot_filter = _filter(symbol, "LOT_SIZE")
        if price_filter is None or lot_filter is None:
            continue

        price_step = Decimal(price_filter["tickSize"])
        size_step = Decimal(lot_filter["stepSize"])
        if price_step <= 0 or size_step <= 0:
            continue

        base = symbol["baseAsset"]
        quote = symbol["quoteAsset"]

        instruments.append(
            {
                "symbol": symbol["symbol"],
                "name": f"{names.get(base, base)} / {names.get(quote, quote)}",
                "category": "crypto",
                "venue": "BINANCE",
                "price_step": _plain(price_step),
                "size_step": _plain(size_step),
                "_quote": quote,
            }
        )

    return instruments


def _cfd(symbol: str, name: str, category: str, price_step: str, size_step: str) -> dict:
    return {
        "symbol": symbol,
        "name": name,
        "category": category,
        "venue": "CFD",
        "price_step": price_step,
        "size_step": size_step,
    }


# Quote currencies a broker prices with three decimals instead of five.
_THREE_DECIMAL_QUOTES = ("JPY", "HUF")

_FOREX = {
    "EURUSD": "Euro / US Dollar",
    "GBPUSD": "British Pound / US Dollar",
    "AUDUSD": "Australian Dollar / US Dollar",
    "NZDUSD": "New Zealand Dollar / US Dollar",
    "USDJPY": "US Dollar / Japanese Yen",
    "USDCHF": "US Dollar / Swiss Franc",
    "USDCAD": "US Dollar / Canadian Dollar",
    "EURGBP": "Euro / British Pound",
    "EURJPY": "Euro / Japanese Yen",
    "EURCHF": "Euro / Swiss Franc",
    "EURAUD": "Euro / Australian Dollar",
    "EURCAD": "Euro / Canadian Dollar",
    "EURNZD": "Euro / New Zealand Dollar",
    "GBPJPY": "British Pound / Japanese Yen",
    "GBPCHF": "British Pound / Swiss Franc",
    "GBPAUD": "British Pound / Australian Dollar",
    "GBPCAD": "British Pound / Canadian Dollar",
    "GBPNZD": "British Pound / New Zealand Dollar",
    "AUDJPY": "Australian Dollar / Japanese Yen",
    "AUDCHF": "Australian Dollar / Swiss Franc",
    "AUDCAD": "Australian Dollar / Canadian Dollar",
    "AUDNZD": "Australian Dollar / New Zealand Dollar",
    "NZDJPY": "New Zealand Dollar / Japanese Yen",
    "NZDCHF": "New Zealand Dollar / Swiss Franc",
    "NZDCAD": "New Zealand Dollar / Canadian Dollar",
    "CADJPY": "Canadian Dollar / Japanese Yen",
    "CADCHF": "Canadian Dollar / Swiss Franc",
    "CHFJPY": "Swiss Franc / Japanese Yen",
    "SGDJPY": "Singapore Dollar / Japanese Yen",
    "USDTRY": "US Dollar / Turkish Lira",
    "EURTRY": "Euro / Turkish Lira",
    "GBPTRY": "British Pound / Turkish Lira",
    "USDZAR": "US Dollar / South African Rand",
    "EURZAR": "Euro / South African Rand",
    "USDMXN": "US Dollar / Mexican Peso",
    "USDSEK": "US Dollar / Swedish Krona",
    "EURSEK": "Euro / Swedish Krona",
    "USDNOK": "US Dollar / Norwegian Krone",
    "EURNOK": "Euro / Norwegian Krone",
    "USDDKK": "US Dollar / Danish Krone",
    "EURDKK": "Euro / Danish Krone",
    "USDPLN": "US Dollar / Polish Zloty",
    "EURPLN": "Euro / Polish Zloty",
    "USDHUF": "US Dollar / Hungarian Forint",
    "EURHUF": "Euro / Hungarian Forint",
    "USDCZK": "US Dollar / Czech Koruna",
    "EURCZK": "Euro / Czech Koruna",
    "USDSGD": "US Dollar / Singapore Dollar",
    "EURSGD": "Euro / Singapore Dollar",
    "USDHKD": "US Dollar / Hong Kong Dollar",
    "EURHKD": "Euro / Hong Kong Dollar",
    "USDCNH": "US Dollar / Chinese Yuan Offshore",
}

_METALS = {
    "XAUUSD": ("Gold / US Dollar", "0.01"),
    "XAGUSD": ("Silver / US Dollar", "0.001"),
    "XPTUSD": ("Platinum / US Dollar", "0.01"),
    "XPDUSD": ("Palladium / US Dollar", "0.01"),
    "XAUEUR": ("Gold / Euro", "0.01"),
    "XAGEUR": ("Silver / Euro", "0.001"),
}

_ENERGY = {
    "XTIUSD": "Crude Oil WTI",
    "XBRUSD": "Crude Oil Brent",
    "XNGUSD": "Natural Gas",
}

_INDICES = {
    "US30": "Dow Jones 30",
    "US100": "Nasdaq 100",
    "US500": "S&P 500",
    "US2000": "Russell 2000",
    "GER40": "DAX 40",
    "UK100": "FTSE 100",
    "FRA40": "CAC 40",
    "EU50": "Euro Stoxx 50",
    "ESP35": "IBEX 35",
    "ITA40": "FTSE MIB 40",
    "NED25": "AEX 25",
    "SUI20": "SMI 20",
    "JP225": "Nikkei 225",
    "AUS200": "ASX 200",
    "HK50": "Hang Seng 50",
}

_STOCKS = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    "NVDA": "NVIDIA Corp.",
    "AMZN": "Amazon.com Inc.",
    "GOOGL": "Alphabet Inc. Class A",
    "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.",
    "AMD": "Advanced Micro Devices",
    "NFLX": "Netflix Inc.",
    "INTC": "Intel Corp.",
    "IBM": "IBM Corp.",
    "ORCL": "Oracle Corp.",
    "CRM": "Salesforce Inc.",
    "ADBE": "Adobe Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "BAC": "Bank of America Corp.",
    "GS": "Goldman Sachs Group",
    "V": "Visa Inc.",
    "MA": "Mastercard Inc.",
    "DIS": "Walt Disney Co.",
    "KO": "Coca-Cola Co.",
    "PEP": "PepsiCo Inc.",
    "WMT": "Walmart Inc.",
    "NKE": "Nike Inc.",
    "BA": "Boeing Co.",
    "XOM": "Exxon Mobil Corp.",
    "CVX": "Chevron Corp.",
    "PFE": "Pfizer Inc.",
    "JNJ": "Johnson & Johnson",
    "MCD": "McDonald's Corp.",
}


def cfd_instruments() -> list[dict]:
    instruments = []

    for symbol, name in _FOREX.items():
        quote = symbol[3:]
        step = "0.001" if quote in _THREE_DECIMAL_QUOTES else "0.00001"
        instruments.append(_cfd(symbol, name, "forex", step, "1"))

    for symbol, (name, step) in _METALS.items():
        instruments.append(_cfd(symbol, name, "metal", step, "0.01"))

    for symbol, name in _ENERGY.items():
        instruments.append(_cfd(symbol, name, "energy", "0.001", "0.01"))

    for symbol, name in _INDICES.items():
        instruments.append(_cfd(symbol, name, "index", "0.01", "0.01"))

    for symbol, name in _STOCKS.items():
        instruments.append(_cfd(symbol, name, "stock", "0.01", "1"))

    return instruments


# What a trader most likely wants before typing anything: the broker set, then
# the liquid crypto quotes, then the long tail. Search still reaches all of it.
_QUOTE_RANK = {"USDT": 0, "USDC": 1, "FDUSD": 2, "TRY": 3, "EUR": 4, "BTC": 5, "ETH": 6}


def _order(item: dict) -> tuple:
    venue_rank = 0 if item["venue"] == "CFD" else 1
    quote_rank = _QUOTE_RANK.get(item.get("_quote", ""), 9)
    return (venue_rank, quote_rank, item["symbol"])


def build() -> list[dict]:
    instruments = cfd_instruments() + binance_instruments()

    seen: dict[str, dict] = {}
    for instrument in instruments:
        existing = seen.get(instrument["symbol"])
        if existing is not None:
            raise SystemExit(
                f"symbol collision: {instrument['symbol']} on "
                f"{existing['venue']} and {instrument['venue']}"
            )

        for field in ("price_step", "size_step"):
            step = Decimal(instrument[field])
            if -step.as_tuple().exponent > MAX_DECIMALS:
                raise SystemExit(
                    f"{instrument['symbol']}.{field} = {step} needs more than "
                    f"{MAX_DECIMALS} decimals"
                )

        seen[instrument["symbol"]] = instrument

    ordered = sorted(instruments, key=_order)
    for instrument in ordered:
        instrument.pop("_quote", None)

    return ordered


def main() -> None:
    print("Syncing instruments…")
    instruments = build()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(instruments, indent=2, ensure_ascii=False) + "\n")

    venues: dict[str, int] = {}
    for instrument in instruments:
        venues[instrument["venue"]] = venues.get(instrument["venue"], 0) + 1

    print(f"  wrote {len(instruments)} instruments to {OUTPUT}")
    for venue, count in sorted(venues.items()):
        print(f"    {venue}: {count}")


if __name__ == "__main__":
    main()
