from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import httpx

from src.env_keys import alpaca_api_key, alpaca_secret_key

logger = logging.getLogger(__name__)


def resolve_expiry(underlying: str, target_dte: int) -> str:
    expirations = _fetch_expirations(underlying, target_dte)
    if not expirations:
        raise ValueError(f"未找到 {underlying} 在 {target_dte} 天附近的期权到期日")

    today = date.today()
    return min(
        expirations,
        key=lambda exp: abs((date.fromisoformat(exp) - today).days - target_dte),
    )


def _fetch_expirations(underlying: str, target_dte: int) -> list[str]:
    key = alpaca_api_key()
    secret = alpaca_secret_key()
    if not key or not secret:
        raise ValueError("需要 Alpaca Key/Secret 以解析到期日")

    today = date.today()
    window_start = today + timedelta(days=max(1, target_dte - 21))
    window_end = today + timedelta(days=target_dte + 21)

    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    params = {
        "underlying_symbols": underlying.upper(),
        "status": "active",
        "expiration_date_gte": window_start.isoformat(),
        "expiration_date_lte": window_end.isoformat(),
        "limit": 1000,
    }

    expirations: set[str] = set()
    page_token: str | None = None

    with httpx.Client(timeout=30.0) as client:
        while True:
            if page_token:
                params["page_token"] = page_token
            response = client.get(
                "https://paper-api.alpaca.markets/v2/options/contracts",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            body = response.json()
            for contract in body.get("option_contracts", []):
                expirations.add(contract["expiration_date"])
            page_token = body.get("next_page_token")
            if not page_token:
                break

    return sorted(expirations)
