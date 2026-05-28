from __future__ import annotations

from src.models import LegQuote, OptionPortfolio, PortfolioSnapshot, Side


def build_snapshot(
    portfolio: OptionPortfolio, leg_quotes: list[LegQuote]
) -> PortfolioSnapshot:
    multiplier = portfolio.multiplier
    cost = 0.0
    market_value = 0.0

    for quote in leg_quotes:
        leg = quote.leg
        sign = 1 if leg.side == Side.LONG else -1
        qty = leg.quantity
        cost += sign * leg.entry_price * qty * multiplier
        market_value += sign * quote.price * qty * multiplier

    pnl = market_value - cost
    pnl_pct = (pnl / abs(cost) * 100) if cost != 0 else None

    return PortfolioSnapshot(
        portfolio=portfolio,
        leg_quotes=leg_quotes,
        cost=cost,
        market_value=market_value,
        pnl=pnl,
        pnl_pct=pnl_pct,
    )
