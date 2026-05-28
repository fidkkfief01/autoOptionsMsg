from __future__ import annotations

import logging
from datetime import datetime

import httpx

from src.env_keys import alpaca_api_key, alpaca_secret_key
from src.models import LegQuote, OptionGreeks, OptionLeg, OptionPortfolio
from src.occ_symbol import leg_to_occ_symbol
from src.option_metrics import enrich_leg_quote
from src.providers.base import QuoteProvider
from src.underlying import fetch_underlying_mid

logger = logging.getLogger(__name__)

DATA_BASE = "https://data.alpaca.markets/v1beta1/options"


class AlpacaQuoteProvider(QuoteProvider):
    def __init__(self, price_field: str = "mid", feed: str = "indicative") -> None:
        self.price_field = price_field
        self.feed = feed
        self._headers = {
            "APCA-API-KEY-ID": alpaca_api_key(),
            "APCA-API-SECRET-KEY": alpaca_secret_key(),
        }

    def quote_portfolio(self, portfolio: OptionPortfolio) -> list[LegQuote]:
        symbols = [leg_to_occ_symbol(leg) for leg in portfolio.legs]
        snapshots = self._fetch_snapshots(symbols)
        underlying = portfolio.legs[0].underlying if portfolio.legs else ""
        spot = fetch_underlying_mid([underlying]).get(underlying) if underlying else None

        quotes: list[LegQuote] = []
        for leg in portfolio.legs:
            symbol = leg_to_occ_symbol(leg)
            if symbol not in snapshots:
                raise ValueError(f"Alpaca 未返回合约 {symbol}")
            quote = self._leg_quote_from_snapshot(leg, snapshots[symbol])
            quotes.append(enrich_leg_quote(quote, spot))
        return quotes

    def quote_leg(self, leg: OptionLeg) -> LegQuote:
        if leg.manual_price is not None:
            spot = fetch_underlying_mid([leg.underlying]).get(leg.underlying)
            quote = LegQuote(
                leg=leg,
                price=leg.manual_price,
                source="manual_override",
            )
            return enrich_leg_quote(quote, spot)

        symbol = leg_to_occ_symbol(leg)
        snapshot = self._fetch_snapshots([symbol]).get(symbol)
        if not snapshot:
            raise ValueError(f"Alpaca 未返回合约 {symbol}")
        spot = fetch_underlying_mid([leg.underlying]).get(leg.underlying)
        return enrich_leg_quote(self._leg_quote_from_snapshot(leg, snapshot), spot)

    def _leg_quote_from_snapshot(self, leg: OptionLeg, snapshot: dict) -> LegQuote:
        quote_data = snapshot.get("latestQuote") or {}
        price = _pick_alpaca_price(quote_data, self.price_field)
        if price is None or price <= 0:
            raise ValueError(f"Alpaca 无效报价: {leg.underlying} strike={leg.strike}")

        greeks_raw = snapshot.get("greeks") or {}
        greeks = OptionGreeks(
            delta=_safe_float(greeks_raw.get("delta")),
            gamma=_safe_float(greeks_raw.get("gamma")),
            theta=_safe_float(greeks_raw.get("theta")),
            vega=_safe_float(greeks_raw.get("vega")),
            rho=_safe_float(greeks_raw.get("rho")),
        )
        iv = _safe_float(snapshot.get("impliedVolatility"))

        return LegQuote(
            leg=leg,
            price=float(price),
            source=f"alpaca:{self.feed}",
            quoted_at=_parse_quote_time(quote_data.get("t")),
            implied_vol=iv,
            greeks=greeks if any(v is not None for v in greeks.model_dump().values()) else None,
        )

    def _fetch_snapshots(self, symbols: list[str]) -> dict[str, dict]:
        if not symbols:
            return {}
        url = f"{DATA_BASE}/snapshots"
        params = {"symbols": ",".join(symbols), "feed": self.feed}
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json().get("snapshots") or {}


def _safe_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _parse_quote_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _pick_alpaca_price(quote: dict, field: str) -> float | None:
    if field == "bid":
        return _safe_float(quote.get("bp"))
    if field == "ask":
        return _safe_float(quote.get("ap"))
    if field == "last":
        return _safe_float(quote.get("lp"))

    bid = _safe_float(quote.get("bp"))
    ask = _safe_float(quote.get("ap"))
    if bid and ask and bid > 0 and ask > 0:
        return (bid + ask) / 2
    return _safe_float(quote.get("lp"))
