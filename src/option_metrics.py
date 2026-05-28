from __future__ import annotations

from src.models import LegQuote, OptionGreeks, OptionType, Side


def intrinsic_value(spot: float, strike: float, option_type: OptionType) -> float:
    if option_type == OptionType.CALL:
        return max(0.0, spot - strike)
    return max(0.0, strike - spot)


def time_value(option_price: float, intrinsic: float) -> float:
    return max(0.0, option_price - intrinsic)


def enrich_leg_quote(quote: LegQuote, spot: float | None) -> LegQuote:
    if spot is None or spot <= 0:
        return quote

    leg = quote.leg
    intr = intrinsic_value(spot, leg.strike, leg.option_type)
    extr = time_value(quote.price, intr)
    return quote.model_copy(
        update={
            "intrinsic_value": intr,
            "time_value": extr,
        }
    )


def net_position_greeks(quotes: list[LegQuote]) -> OptionGreeks | None:
    delta = gamma = theta = vega = rho = 0.0
    has_any = False

    for quote in quotes:
        if quote.greeks is None:
            continue
        sign = 1 if quote.leg.side == Side.LONG else -1
        qty = quote.leg.quantity
        g = quote.greeks
        if g.delta is not None:
            delta += sign * qty * g.delta
            has_any = True
        if g.gamma is not None:
            gamma += sign * qty * g.gamma
        if g.theta is not None:
            theta += sign * qty * g.theta
        if g.vega is not None:
            vega += sign * qty * g.vega
        if g.rho is not None:
            rho += sign * qty * g.rho

    if not has_any:
        return None

    return OptionGreeks(
        delta=delta,
        gamma=gamma,
        theta=theta,
        vega=vega,
        rho=rho,
    )
