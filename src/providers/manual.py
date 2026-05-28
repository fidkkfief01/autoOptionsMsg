from __future__ import annotations

from src.models import LegQuote, OptionLeg
from src.providers.base import QuoteProvider


class ManualQuoteProvider(QuoteProvider):
    def quote_leg(self, leg: OptionLeg) -> LegQuote:
        if leg.manual_price is None:
            raise ValueError(
                f"manual 模式需要设置 manual_price: "
                f"{leg.underlying} {leg.expiry} {leg.strike}"
            )
        return LegQuote(leg=leg, price=leg.manual_price, source="manual")
