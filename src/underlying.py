from __future__ import annotations

import logging

import httpx

from src.env_keys import alpaca_api_key, alpaca_secret_key

logger = logging.getLogger(__name__)


def fetch_underlying_mid(symbols: list[str]) -> dict[str, float]:
    key = alpaca_api_key()
    secret = alpaca_secret_key()
    if not key or not secret:
        return {}

    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    result: dict[str, float] = {}

    with httpx.Client(timeout=20.0) as client:
        for symbol in symbols:
            try:
                response = client.get(
                    f"https://data.alpaca.markets/v2/stocks/{symbol}/snapshot",
                    headers=headers,
                )
                response.raise_for_status()
                price = _pick_stock_mid(response.json())
                if price is not None:
                    result[symbol] = price
            except Exception:
                logger.exception("获取标的 %s 现价失败", symbol)

    return result


def _pick_stock_mid(snapshot: dict) -> float | None:
    quote = snapshot.get("latestQuote") or {}
    bid = _safe(quote.get("bp"))
    ask = _safe(quote.get("ap"))
    if bid and ask and bid > 0 and ask > 0:
        return (bid + ask) / 2

    trade = snapshot.get("latestTrade") or {}
    last = _safe(trade.get("p"))
    if last and last > 0:
        return last

    bar = snapshot.get("dailyBar") or snapshot.get("prevDailyBar") or {}
    return _safe(bar.get("c"))


def _safe(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number
