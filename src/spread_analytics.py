from __future__ import annotations

from dataclasses import dataclass

from src.models import LegQuote, OptionPortfolio, OptionType, PortfolioSnapshot, Side


@dataclass(frozen=True)
class SpreadMetrics:
    spread_type: str
    underlying: str
    spread_units: int
    strike_low: float
    strike_high: float
    strike_midpoint: float
    spread_width: float
    underlying_price: float | None
    entry_net_per_share: float
    current_mid_per_share: float
    max_profit: float
    max_loss: float
    breakeven: float
    distance_to_mid: float | None


def analyze_vertical_spread(
    snapshot: PortfolioSnapshot,
    underlying_price: float | None = None,
) -> SpreadMetrics | None:
    quotes = snapshot.leg_quotes
    if len(quotes) != 2:
        return None

    legs = [q.leg for q in quotes]
    if not (
        legs[0].underlying == legs[1].underlying
        and legs[0].expiry == legs[1].expiry
        and legs[0].option_type == legs[1].option_type
        and legs[0].quantity == legs[1].quantity
    ):
        return None

    spread_units = legs[0].quantity
    multiplier = snapshot.portfolio.multiplier
    k_low = min(legs[0].strike, legs[1].strike)
    k_high = max(legs[0].strike, legs[1].strike)
    width = k_high - k_low
    strike_mid = (k_low + k_high) / 2

    entry_net = _net_per_share(quotes, use_entry=True)
    current_mid = _net_per_share(quotes, use_entry=False)

    spread_type = _detect_spread_type(quotes)
    if spread_type is None:
        return None

    if entry_net >= 0:
        max_profit_per_share = width - entry_net
        max_loss_per_share = entry_net
    else:
        credit = -entry_net
        max_profit_per_share = credit
        max_loss_per_share = width - credit

    if max_profit_per_share <= 0 or max_loss_per_share <= 0:
        return None

    breakeven = _breakeven(spread_type, k_low, k_high, abs(entry_net), entry_net >= 0)
    distance = (
        underlying_price - strike_mid if underlying_price is not None else None
    )

    return SpreadMetrics(
        spread_type=spread_type,
        underlying=legs[0].underlying,
        spread_units=spread_units,
        strike_low=k_low,
        strike_high=k_high,
        strike_midpoint=strike_mid,
        spread_width=width,
        underlying_price=underlying_price,
        entry_net_per_share=entry_net,
        current_mid_per_share=current_mid,
        max_profit=max_profit_per_share * multiplier * spread_units,
        max_loss=max_loss_per_share * multiplier * spread_units,
        breakeven=breakeven,
        distance_to_mid=distance,
    )


def _net_per_share(quotes: list[LegQuote], *, use_entry: bool) -> float:
    total = 0.0
    for quote in quotes:
        leg = quote.leg
        sign = 1 if leg.side == Side.LONG else -1
        price = leg.entry_price if use_entry else quote.price
        total += sign * price
    return total


def _detect_spread_type(quotes: list[LegQuote]) -> str | None:
    long_leg = next((q for q in quotes if q.leg.side == Side.LONG), None)
    short_leg = next((q for q in quotes if q.leg.side == Side.SHORT), None)
    if not long_leg or not short_leg:
        return None

    if long_leg.leg.option_type == OptionType.CALL:
        if long_leg.leg.strike < short_leg.leg.strike:
            return "bull_call"
        if long_leg.leg.strike > short_leg.leg.strike:
            return "bear_call"
    else:
        if long_leg.leg.strike > short_leg.leg.strike:
            return "bear_put"
        if long_leg.leg.strike < short_leg.leg.strike:
            return "bull_put"
    return None


def _breakeven(
    spread_type: str,
    k_low: float,
    k_high: float,
    premium: float,
    is_debit: bool,
) -> float:
    if spread_type == "bull_call":
        return k_low + premium
    if spread_type == "bear_call":
        return k_low + premium if not is_debit else k_high - premium
    if spread_type == "bear_put":
        return k_high - premium
    if spread_type == "bull_put":
        return k_low + premium if is_debit else k_high - premium
    return k_low + premium


_SPREAD_TYPE_LABEL = {
    "bull_call": "牛市看涨价差",
    "bear_call": "熊市看涨价差",
    "bear_put": "熊市看跌价差",
    "bull_put": "牛市看跌价差",
}


def spread_type_label(spread_type: str) -> str:
    return _SPREAD_TYPE_LABEL.get(spread_type, spread_type)
