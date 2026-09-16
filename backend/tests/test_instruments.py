from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ..app.main import app
from ..app.core.instruments import INSTRUMENTS, get_instrument, is_on_step
from ..app.schemas.trade import TradeCreate


client = TestClient(app)


def test_instruments_endpoint_needs_no_token():
    response = client.get("/api/v1/instruments/")

    assert response.status_code == 200

    payload = response.json()
    symbols = [item["symbol"] for item in payload]

    assert len(payload) == len(INSTRUMENTS)
    assert "BTCUSDT" in symbols
    assert "EURUSD" in symbols

    bitcoin = next(item for item in payload if item["symbol"] == "BTCUSDT")

    assert bitcoin["category"] == "crypto"
    assert bitcoin["venue"] == "BINANCE"
    assert bitcoin["price_step"] == "0.01"
    assert bitcoin["size_step"] == "0.00001"

    euro = next(item for item in payload if item["symbol"] == "EURUSD")

    assert euro["category"] == "forex"
    assert euro["venue"] == "CFD"
    assert euro["price_step"] == "0.00001"

    # Steps reach the client as plain decimals; 1E-8 would parse as NaN.
    assert all("E" not in item["price_step"].upper() for item in payload)


def test_catalog_covers_both_venues():
    venues = {instrument.venue for instrument in INSTRUMENTS}

    assert venues == {"BINANCE", "CFD"}
    assert sum(1 for i in INSTRUMENTS if i.venue == "BINANCE") > 1000
    assert get_instrument("SHIBUSDT").price_step == Decimal("0.00000001")


def test_catalog_symbols_are_unique_and_steps_are_positive():
    symbols = [instrument.symbol for instrument in INSTRUMENTS]

    assert len(symbols) == len(set(symbols))

    for instrument in INSTRUMENTS:
        assert instrument.price_step > 0
        assert instrument.size_step > 0
        # The trades table stores Numeric(28, 10).
        assert -instrument.price_step.as_tuple().exponent <= 10
        assert -instrument.size_step.as_tuple().exponent <= 10


def test_trade_create_uppercases_a_known_symbol():
    trade = TradeCreate(
        instrument="btcusdt",
        is_long=True,
        entry_price=Decimal("50000.00"),
        position_size=Decimal("0.1000"),
    )

    assert trade.instrument == "BTCUSDT"


def test_trade_create_rejects_unknown_instrument():
    with pytest.raises(ValidationError, match="Unknown instrument"):
        TradeCreate(
            instrument="MADEUPCOIN",
            is_long=True,
            entry_price=Decimal("10"),
            position_size=Decimal("1"),
        )


def test_trade_create_rejects_price_off_the_instrument_step():
    # BTCUSDT moves in cents, so a third decimal is not a price we can store.
    with pytest.raises(ValidationError, match="entry_price must be a multiple of 0.01"):
        TradeCreate(
            instrument="BTCUSDT",
            is_long=True,
            entry_price=Decimal("50000.123"),
            position_size=Decimal("0.1"),
        )


def test_trade_create_rejects_stop_and_target_off_step():
    with pytest.raises(ValidationError, match="stop_loss must be a multiple of 0.01"):
        TradeCreate(
            instrument="BTCUSDT",
            is_long=True,
            entry_price=Decimal("50000.00"),
            position_size=Decimal("0.1"),
            stop_loss=Decimal("49000.005"),
        )

    with pytest.raises(ValidationError, match="take_profit must be a multiple of 0.01"):
        TradeCreate(
            instrument="BTCUSDT",
            is_long=True,
            entry_price=Decimal("50000.00"),
            position_size=Decimal("0.1"),
            take_profit=Decimal("52000.005"),
        )


def test_trade_create_rejects_position_size_off_step():
    # Forex positions are journaled in whole units.
    with pytest.raises(ValidationError, match="position_size must be a multiple of 1"):
        TradeCreate(
            instrument="EURUSD",
            is_long=True,
            entry_price=Decimal("1.1000"),
            position_size=Decimal("1000.5"),
        )


def test_is_on_step_matches_the_catalog():
    gold = get_instrument("XAUUSD")

    assert gold is not None
    assert is_on_step(Decimal("2400.25"), gold.price_step)
    assert not is_on_step(Decimal("2400.255"), gold.price_step)


def test_eight_decimal_prices_survive_validation():
    """The reason the columns were widened: SHIBUSDT ticks at 1e-8."""
    trade = TradeCreate(
        instrument="SHIBUSDT",
        is_long=True,
        entry_price=Decimal("0.00001234"),
        position_size=Decimal("1000000"),
        stop_loss=Decimal("0.00001180"),
        take_profit=Decimal("0.00001400"),
    )

    assert trade.entry_price == Decimal("0.00001234")

    with pytest.raises(ValidationError, match="entry_price must be a multiple"):
        TradeCreate(
            instrument="SHIBUSDT",
            is_long=True,
            entry_price=Decimal("0.000012345"),
            position_size=Decimal("1000000"),
        )
