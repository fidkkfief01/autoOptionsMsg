from __future__ import annotations

from src.expiry_resolver import resolve_expiry
from src.leg_parser import LegParseError, parse_spread_command
from src.models import AppConfig, LegQuote, OptionLeg, OptionPortfolio, PortfolioSnapshot
from src.pnl import build_snapshot
from src.providers import AlpacaQuoteProvider, ManualQuoteProvider, YFinanceQuoteProvider
from src.providers.base import QuoteProvider
from src.telegram_notifier import NotifyContext, TelegramNotifier
from src.underlying import fetch_underlying_mid


class SpreadQueryService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.provider = _build_provider(config)
        self.notifier = TelegramNotifier(
            bot_token=config.telegram.bot_token,
            chat_id=config.telegram.chat_id,
        )
        self.default_underlying = config.default_underlying

    @classmethod
    def from_config_file(cls, path: str) -> "SpreadQueryService":
        from src.config_loader import load_config

        return cls(load_config(path))

    def handle_command(self, text: str) -> str:
        try:
            parsed = parse_spread_command(text, self.default_underlying)
            expiry = resolve_expiry(parsed.underlying, parsed.target_dte)
            legs = [
                leg.model_copy(update={"expiry": expiry, "underlying": parsed.underlying})
                for leg in parsed.legs
            ]
            portfolio = OptionPortfolio(
                name=f"{parsed.underlying} 查询 ({expiry})",
                multiplier=100,
                legs=legs,
            )

            raw_quotes = self.provider.quote_portfolio(portfolio)
            quotes = [
                q.model_copy(
                    update={"leg": q.leg.model_copy(update={"entry_price": q.price})}
                )
                for q in raw_quotes
            ]
            snapshot = build_snapshot(portfolio, quotes)
            spot = fetch_underlying_mid([parsed.underlying]).get(parsed.underlying)
            ctx = NotifyContext(
                provider=self.config.provider,
                price_field=self.config.price_field,
                alpaca_feed=self.config.alpaca_feed
                if self.config.provider == "alpaca"
                else None,
            )

            header = _format_query_header(parsed, expiry)
            body = self.notifier.format_snapshots([snapshot], ctx=ctx, underlying_prices={parsed.underlying: spot} if spot else {})
            return f"{header}\n\n{body}"
        except LegParseError as exc:
            return _format_error(str(exc))
        except Exception as exc:
            return _format_error(f"查询失败：{exc}")


def _format_query_header(parsed, expiry: str) -> str:
    from datetime import date

    today = date.today()
    actual_dte = (date.fromisoformat(expiry) - today).days
    legs_txt = ", ".join(
        f"{'+' if leg.side.value == 'long' else '-'}{leg.quantity} "
        f"{leg.strike:g}{'C' if leg.option_type.value == 'call' else 'P'}"
        for leg in parsed.legs
    )
    return (
        "🔍 <b>期权查询结果</b>\n"
        f"输入: <code>{parsed.underlying} {legs_txt}, {parsed.target_dte}天</code>\n"
        f"匹配到期日: <code>{expiry}</code>（实际 DTE <b>{actual_dte}</b> 天）"
    )


def _format_error(message: str) -> str:
    return (
        "⚠️ <b>无法解析</b>\n"
        f"{message}\n\n"
        "<b>格式示例</b>\n"
        "<code>QQQ +1 730C, -1 750C, 60天</code>\n"
        "<code>+1 740C, -1 760C, 45d</code>"
    )


def _build_provider(config: AppConfig) -> QuoteProvider:
    if config.provider == "manual":
        return ManualQuoteProvider()
    if config.provider == "yfinance":
        return YFinanceQuoteProvider(price_field=config.price_field)
    return AlpacaQuoteProvider(
        price_field=config.price_field,
        feed=config.alpaca_feed,
    )
