from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import LegQuote, OptionLeg, OptionPortfolio


class QuoteProvider(ABC):
    @abstractmethod
    def quote_leg(self, leg: OptionLeg) -> LegQuote:
        raise NotImplementedError

    def quote_portfolio(self, portfolio: OptionPortfolio) -> list[LegQuote]:
        return [self.quote_leg(leg) for leg in portfolio.legs]
