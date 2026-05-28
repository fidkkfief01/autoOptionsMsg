from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


class Side(str, Enum):
    LONG = "long"
    SHORT = "short"


class OptionLeg(BaseModel):
    underlying: str
    expiry: str
    strike: float
    option_type: OptionType
    side: Side
    quantity: int = Field(gt=0)
    entry_price: float = Field(ge=0)
    manual_price: float | None = Field(default=None, ge=0)

    @field_validator("underlying")
    @classmethod
    def normalize_underlying(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("expiry")
    @classmethod
    def normalize_expiry(cls, value: str) -> str:
        return value.strip()


class OptionPortfolio(BaseModel):
    name: str
    multiplier: int = Field(default=100, gt=0)
    legs: list[OptionLeg] = Field(min_length=1)


class OptionGreeks(BaseModel):
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None


class LegQuote(BaseModel):
    leg: OptionLeg
    price: float
    source: str
    quoted_at: datetime | None = None
    intrinsic_value: float | None = None
    time_value: float | None = None
    implied_vol: float | None = None
    greeks: OptionGreeks | None = None


class PortfolioSnapshot(BaseModel):
    portfolio: OptionPortfolio
    leg_quotes: list[LegQuote]
    cost: float
    market_value: float
    pnl: float
    pnl_pct: float | None


class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str


class AppConfig(BaseModel):
    interval_seconds: int = Field(default=300, ge=30)
    notify_on_start: bool = True
    provider: Literal["alpaca", "yfinance", "manual"] = "alpaca"
    price_field: Literal["mid", "last", "bid", "ask"] = "mid"
    alpaca_feed: Literal["indicative", "opra"] = "indicative"
    default_underlying: str = "QQQ"
    telegram: TelegramConfig
    portfolios: list[OptionPortfolio] = Field(min_length=1)
