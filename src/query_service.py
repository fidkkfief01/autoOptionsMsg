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
            expiry_by_dte = {
                dte: resolve_expiry(parsed.underlying, dte)
                for dte in sorted(set(parsed.leg_dtes))
            }
            legs = [
                leg.model_copy(
                    update={
                        "expiry": expiry_by_dte[dte],
                        "underlying": parsed.underlying,
                    }
                )
                for leg, dte in zip(parsed.legs, parsed.leg_dtes)
            ]
            expiries = [leg.expiry for leg in legs]
            expiry_label = expiries[0] if len(set(expiries)) == 1 else "多到期日"
            portfolio = OptionPortfolio(
                name=f"{parsed.underlying} 查询 ({expiry_label})",
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

            header = _format_query_header(parsed, legs)
            body = self.notifier.format_snapshots([snapshot], ctx=ctx, underlying_prices={parsed.underlying: spot} if spot else {})
            return f"{header}\n\n{body}"
        except LegParseError as exc:
            return _format_error(str(exc))
        except Exception as exc:
            return _format_error(f"查询失败：{exc}")


def _format_query_header(parsed, legs: list[OptionLeg]) -> str:
    from datetime import date

    today = date.today()
    legs_txt_parts = []
    expiry_lines = []
    for leg, target_dte in zip(legs, parsed.leg_dtes):
        cp = "C" if leg.option_type.value == "call" else "P"
        side = "+" if leg.side.value == "long" else "-"
        actual_dte = (date.fromisoformat(leg.expiry) - today).days
        legs_txt_parts.append(f"{side}{leg.quantity} {leg.strike:g}{cp}, {target_dte}天")
        expiry_lines.append(
            f"• <code>{side}{leg.quantity} {leg.strike:g}{cp}</code> → "
            f"<code>{leg.expiry}</code>（目标 {target_dte}天 / 实际 <b>{actual_dte}</b> 天）"
        )
    legs_txt = ", ".join(legs_txt_parts)
    expiry_text = "\n".join(expiry_lines)
    return (
        "🔍 <b>期权查询结果</b>\n"
        f"输入: <code>{parsed.underlying} {legs_txt}</code>\n"
        f"匹配到期日:\n{expiry_text}"
    )


def _format_error(message: str) -> str:
    return (
        "⚠️ <b>无法解析</b>\n"
        f"{message}\n\n"
        "<b>格式示例</b>\n"
        "<code>QQQ +1 730C, -1 750C, 60天</code>\n"
        "<code>QQQ +1 730C,59天,-1 750C,307天</code>\n"
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
