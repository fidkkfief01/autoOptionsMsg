from __future__ import annotations

import logging

from src.config_loader import load_config
from src.env_keys import telegram_bot_token, telegram_chat_id
from src.models import AppConfig, PortfolioSnapshot
from src.pnl import build_snapshot
from src.providers import (
    AlpacaQuoteProvider,
    ManualQuoteProvider,
    QuoteProvider,
    YFinanceQuoteProvider,
)
from src.telegram_notifier import NotifyContext, TelegramNotifier
from src.underlying import fetch_underlying_mid

logger = logging.getLogger(__name__)


class OptionsMonitorService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.provider = _build_provider(config)
        tg = config.telegram
        self.notifier = TelegramNotifier(
            bot_token=tg.bot_token or telegram_bot_token(),
            chat_id=tg.chat_id or telegram_chat_id(),
        )

    @classmethod
    def from_config_file(cls, path: str) -> "OptionsMonitorService":
        return cls(load_config(path))

    def poll_once(self, send_telegram: bool = True) -> list[PortfolioSnapshot]:
        snapshots: list[PortfolioSnapshot] = []
        errors: list[str] = []

        for portfolio in self.config.portfolios:
            try:
                quotes = self.provider.quote_portfolio(portfolio)
                snapshot = build_snapshot(portfolio, quotes)
                snapshots.append(snapshot)
                logger.info(
                    "%s | cost=%.2f mv=%.2f pnl=%.2f",
                    portfolio.name,
                    snapshot.cost,
                    snapshot.market_value,
                    snapshot.pnl,
                )
            except Exception as exc:
                logger.exception("组合 %s 查询失败", portfolio.name)
                errors.append(f"{portfolio.name}: {exc}")

        if snapshots:
            symbols = {
                q.leg.underlying
                for s in snapshots
                for q in s.leg_quotes
            }
            underlying_prices = fetch_underlying_mid(sorted(symbols))
            ctx = NotifyContext(
                provider=self.config.provider,
                price_field=self.config.price_field,
                alpaca_feed=self.config.alpaca_feed
                if self.config.provider == "alpaca"
                else None,
            )
            message = self.notifier.format_snapshots(
                snapshots, ctx=ctx, underlying_prices=underlying_prices
            )
            print(_plain_text(message))
            if send_telegram:
                self.notifier.notify_snapshots(
                    snapshots, ctx=ctx, underlying_prices=underlying_prices
                )

        if send_telegram and errors:
            self.notifier.send_message(
                "<b>部分组合查询失败</b>\n" + "\n".join(f"• {e}" for e in errors)
            )

        return snapshots


def _build_provider(config: AppConfig) -> QuoteProvider:
    if config.provider == "manual":
        return ManualQuoteProvider()
    if config.provider == "yfinance":
        return YFinanceQuoteProvider(price_field=config.price_field)
    return AlpacaQuoteProvider(
        price_field=config.price_field,
        feed=config.alpaca_feed,
    )


def _plain_text(html: str) -> str:
    for tag in ("<b>", "</b>", "<i>", "</i>", "<code>", "</code>"):
        html = html.replace(tag, "")
    return html
