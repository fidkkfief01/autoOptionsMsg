from __future__ import annotations

from functools import lru_cache

import yfinance as yf

from src.models import LegQuote, OptionLeg, OptionType
from src.option_metrics import enrich_leg_quote
from src.providers.base import QuoteProvider
from src.underlying import fetch_underlying_mid


class YFinanceQuoteProvider(QuoteProvider):
    def __init__(self, price_field: str = "mid") -> None:
        self.price_field = price_field

    def quote_leg(self, leg: OptionLeg) -> LegQuote:
        if leg.manual_price is not None:
            spot = fetch_underlying_mid([leg.underlying]).get(leg.underlying)
            return enrich_leg_quote(
                LegQuote(leg=leg, price=leg.manual_price, source="manual_override"),
                spot,
            )

        chain = _get_chain(leg.underlying, leg.expiry)
        table = chain.calls if leg.option_type == OptionType.CALL else chain.puts
        row = table[table["strike"] == leg.strike]
        if row.empty:
            raise ValueError(f"未找到合约: {leg.underlying} {leg.expiry} strike={leg.strike}")

        record = row.iloc[0]
        price = _pick_price(record, self.price_field)
        if price is None or price <= 0:
            raise ValueError(f"无效报价: {leg.underlying} {leg.expiry} strike={leg.strike}")

        iv = _safe_float(record.get("impliedVolatility"))
        spot = fetch_underlying_mid([leg.underlying]).get(leg.underlying)
        quote = LegQuote(
            leg=leg,
            price=float(price),
            source="yfinance",
            implied_vol=iv,
        )
        return enrich_leg_quote(quote, spot)


@lru_cache(maxsize=64)
def _get_chain(underlying: str, expiry: str):
    ticker = yf.Ticker(underlying)
    if expiry not in ticker.options:
        raise ValueError(f"{underlying} 无到期日 {expiry}")
    return ticker.option_chain(expiry)


def _pick_price(record, field: str) -> float | None:
    if field == "last":
        return _safe_float(record.get("lastPrice"))
    if field == "bid":
        return _safe_float(record.get("bid"))
    if field == "ask":
        return _safe_float(record.get("ask"))

    bid = _safe_float(record.get("bid"))
    ask = _safe_float(record.get("ask"))
    if bid and ask and bid > 0 and ask > 0:
        return (bid + ask) / 2
    return _safe_float(record.get("lastPrice"))


def _safe_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number
