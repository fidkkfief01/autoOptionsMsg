from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import httpx

from src.models import LegQuote, OptionGreeks, OptionType, PortfolioSnapshot, Side
from src.option_metrics import net_position_greeks
from src.spread_analytics import SpreadMetrics, analyze_vertical_spread, spread_type_label

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")
SEP = "────────────────────────"

_PRICE_FIELD_SHORT = {
    "mid": "买卖中间价",
    "last": "最新成交价",
    "bid": "买一价",
    "ask": "卖一价",
}

_FEED_SHORT = {
    "indicative": "Alpaca 指示性 · 盘中约延迟15分钟",
    "opra": "Alpaca OPRA 实时",
}


@dataclass(frozen=True)
class NotifyContext:
    provider: str
    price_field: str
    alpaca_feed: str | None = None

    @property
    def feed_short(self) -> str:
        if self.provider == "alpaca":
            return _FEED_SHORT.get(self.alpaca_feed or "indicative", self.alpaca_feed or "")
        if self.provider == "yfinance":
            return "Yahoo Finance · 非官方"
        if self.provider == "manual":
            return "手动填价"
        return self.provider

    @property
    def price_short(self) -> str:
        return _PRICE_FIELD_SHORT.get(self.price_field, self.price_field)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._api_base = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str) -> None:
        if not self.bot_token or not self.chat_id:
            raise ValueError("未配置 TG_BOT_TOKEN / TG_CHAT_ID，无法发送 Telegram 通知")

        url = f"{self._api_base}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError(f"Telegram API 错误: {body}")

    def format_snapshots(
        self,
        snapshots: list[PortfolioSnapshot],
        ctx: NotifyContext | None = None,
        underlying_prices: dict[str, float] | None = None,
    ) -> str:
        now_et = datetime.now(ET)
        prices = underlying_prices or {}
        blocks = [_format_header(now_et, ctx)]
        for snapshot in snapshots:
            underlying = snapshot.leg_quotes[0].leg.underlying if snapshot.leg_quotes else ""
            spot = prices.get(underlying)
            blocks.append(_format_snapshot(snapshot, spot))
        return "\n\n".join(blocks)

    def notify_snapshots(
        self,
        snapshots: list[PortfolioSnapshot],
        ctx: NotifyContext | None = None,
        underlying_prices: dict[str, float] | None = None,
    ) -> None:
        self.send_message(
            self.format_snapshots(snapshots, ctx=ctx, underlying_prices=underlying_prices)
        )


def _format_header(now_et: datetime, ctx: NotifyContext | None) -> str:
    lines = [
        "📊 <b>期权盈亏播报</b>",
        SEP,
        f"🕐 <b>统计时间</b>  <code>{now_et.strftime('%Y-%m-%d %H:%M:%S')} ET</code>",
    ]
    if ctx:
        lines.append(f"📡 <b>行情来源</b>  {_escape(ctx.feed_short)}")
        lines.append(f"💹 <b>计价方式</b>  {_escape(ctx.price_short)}")
    return "\n".join(lines)


def _format_snapshot(
    snapshot: PortfolioSnapshot,
    underlying_price: float | None = None,
) -> str:
    p = snapshot.portfolio
    multiplier = p.multiplier
    pnl_icon = _pnl_icon(snapshot.pnl)
    pnl_sign = "+" if snapshot.pnl >= 0 else ""
    pct_line = ""
    if snapshot.pnl_pct is not None:
        pct_line = f"\n┃ 收益率      <code>{pnl_sign}{snapshot.pnl_pct:.2f}%</code>"

    metrics = analyze_vertical_spread(snapshot, underlying_price)
    spread = _format_spread_banner(snapshot, metrics)
    max_lag = _max_quote_lag(snapshot.leg_quotes)

    lines = [
        "════════════════════════",
        f"📌 <b>{_escape(p.name)}</b>",
        "════════════════════════",
    ]
    if spread:
        lines.extend([spread, ""])

    if metrics:
        lines.extend(_format_metrics_block(snapshot, metrics))
        lines.append("")

    lines.extend(
        [
            "┏ <b>组合汇总</b> <i>(美元 · 未实现)</i>",
            f"┃ 净建仓成本  <code>{_money_plain(snapshot.cost)}</code>  <i>开仓净支出</i>",
            f"┃ 当前市值    <code>{_money_plain(snapshot.market_value)}</code>  <i>按现价估算</i>",
            f"┃ 浮动盈亏    <code>{pnl_sign}{_money_plain(snapshot.pnl)}</code>  {pnl_icon}{pct_line}",
            "┗" + "━" * 22,
            f"📦 合约乘数  <code>{multiplier}</code>  <i>(每张 = {multiplier} 股名义)</i>",
        ]
    )

    if max_lag:
        lines.append(f"⏱ <b>报价延迟</b>  <i>{max_lag}</i>")

    net_greeks = net_position_greeks(snapshot.leg_quotes)
    if net_greeks:
        lines.extend(["", _format_net_greeks_block(net_greeks)])

    lines.extend(["", "<b>📋 各腿明细</b>"])
    for index, quote in enumerate(snapshot.leg_quotes, start=1):
        lines.append(_format_leg_card(index, quote, multiplier))

    return "\n".join(lines)


def _format_metrics_block(snapshot: PortfolioSnapshot, m: SpreadMetrics) -> list[str]:
    dist_sign = "+" if (m.distance_to_mid or 0) >= 0 else ""
    dist_line = ""
    if m.underlying_price is not None and m.distance_to_mid is not None:
        dist_line = (
            f"\n┃ 现价距中点  <code>{dist_sign}{_money_plain(m.distance_to_mid)}</code>"
            "  <i>(标的−行权中点)</i>"
        )

    profit_hint = ""
    if m.max_profit > 0:
        captured = max(0.0, min(100.0, snapshot.pnl / m.max_profit * 100))
        profit_hint = f"  <i>(当前浮盈占最大盈利 {captured:.0f}%)</i>"

    lines = ["┏ <b>价差分析</b>"]
    if m.underlying_price is not None:
        lines.append(
            f"┃ 标的现价    <code>{_money_plain(m.underlying_price)}</code>  <i>现货 mid</i>"
        )
    lines.extend(
        [
            f"┃ 行权价中点  <code>{_money_plain(m.strike_midpoint)}</code>"
            f"  <i>({m.strike_low:g}与{m.strike_high:g}的中点)</i>{dist_line}",
            f"┃ 组合中间价  <code>{_money_plain(m.current_mid_per_share)}</code>/张"
            "  <i>净权利金 mid = 多腿−空腿</i>",
            f"┃ 建仓净价    <code>{_money_plain(m.entry_net_per_share)}</code>/张"
            "  <i>开仓净借方</i>",
            f"┃ 最大盈利    <code>{_money_plain(m.max_profit)}</code>"
            f"  <i>(到期理论上限)</i>{profit_hint}",
            f"┃ 最大亏损    <code>{_money_plain(m.max_loss)}</code>"
            "  <i>(到期理论下限)</i>",
            f"┃ 盈亏平衡    <code>{_money_plain(m.breakeven)}</code>"
            "  <i>(到期刚好打平)</i>",
            "┗" + "━" * 22,
        ]
    )
    return lines


def _format_spread_banner(
    snapshot: PortfolioSnapshot,
    metrics: SpreadMetrics | None,
) -> str:
    legs = [q.leg for q in snapshot.leg_quotes]
    if len(legs) != 2:
        return ""

    if not (
        legs[0].expiry == legs[1].expiry
        and legs[0].option_type == legs[1].option_type
        and legs[0].underlying == legs[1].underlying
    ):
        return ""

    dte = _days_to_expiry(legs[0].expiry)
    label = spread_type_label(metrics.spread_type) if metrics else (
        "看涨价差" if legs[0].option_type == OptionType.CALL else "看跌价差"
    )
    width = metrics.spread_width if metrics else abs(legs[0].strike - legs[1].strike)
    return (
        f"📐 <b>{legs[0].underlying}</b> {label}\n"
        f"    到期 <code>{legs[0].expiry}</code>  ·  <b>DTE {dte}天</b>  ·  "
        f"宽度 <code>${width:g}</code>"
    )


def _format_leg_card(index: int, quote: LegQuote, multiplier: int) -> str:
    leg = quote.leg
    dte = _days_to_expiry(leg.expiry)
    is_long = leg.side == Side.LONG
    side_icon = "🟢" if is_long else "🔴"
    side_txt = "买入 Long" if is_long else "卖出 Short"
    opt = "Call 看涨" if leg.option_type == OptionType.CALL else "Put 看跌"
    sign = 1 if is_long else -1
    leg_pnl = sign * (quote.price - leg.entry_price) * leg.quantity * multiplier
    pnl_sign = "+" if leg_pnl >= 0 else ""
    pnl_icon = _pnl_icon(leg_pnl)

    lag_line = ""
    if quote.quoted_at:
        lag_line = f"\n   ⏱ {_format_lag(quote.quoted_at)}"

    value_line = _format_value_line(quote)
    greeks_line = _format_greeks_line(quote.greeks, quote.implied_vol)

    lines = [
        f"\n{side_icon} <b>腿{index}</b>  <code>{leg.underlying}</code>  {opt}  "
        f"<code>${leg.strike:g}</code>",
        f"   {side_txt}  ·  <code>{leg.quantity}</code>张  ·  "
        f"到期 <code>{leg.expiry}</code> (<b>DTE {dte}天</b>)",
        f"   建仓 <code>{_money_plain(leg.entry_price)}</code>  →  "
        f"现价 <code>{_money_plain(quote.price)}</code>",
        f"   本腿盈亏  <code>{pnl_sign}{_money_plain(leg_pnl)}</code>  {pnl_icon}",
    ]
    if value_line:
        lines.append(value_line)
    if greeks_line:
        lines.append(greeks_line)
    if lag_line:
        lines.append(lag_line.lstrip())
    return "\n".join(lines)


def _format_value_line(quote: LegQuote) -> str:
    if quote.intrinsic_value is None or quote.time_value is None:
        return ""
    return (
        "   价值构成  内在价值 "
        f"<code>{_money_plain(quote.intrinsic_value)}</code>/张  ·  "
        "时间价值 "
        f"<code>{_money_plain(quote.time_value)}</code>/张"
        "  <i>(现价−内在)</i>"
    )


def _format_greeks_line(greeks: OptionGreeks | None, iv: float | None) -> str:
    parts: list[str] = []
    if iv is not None:
        parts.append(f"IV <code>{iv * 100:.1f}%</code>")
    if greeks:
        if greeks.delta is not None:
            parts.append(f"Δ <code>{greeks.delta:+.4f}</code>")
        if greeks.gamma is not None:
            parts.append(f"Γ <code>{greeks.gamma:.4f}</code>")
        if greeks.theta is not None:
            parts.append(f"Θ <code>{greeks.theta:+.4f}</code>")
        if greeks.vega is not None:
            parts.append(f"V <code>{greeks.vega:.4f}</code>")
        if greeks.rho is not None:
            parts.append(f"ρ <code>{greeks.rho:+.4f}</code>")
    if not parts:
        return ""
    return "   希腊值  " + "  ·  ".join(parts) + "  <i>(单张合约)</i>"


def _format_net_greeks_block(net: OptionGreeks) -> str:
    lines = [
        "┏ <b>组合净希腊值</b> <i>(方向×张数加权)</i>",
    ]
    if net.delta is not None:
        lines.append(f"┃ Delta  <code>{net.delta:+.4f}</code>  <i>标的涨跌敏感度</i>")
    if net.gamma is not None:
        lines.append(f"┃ Gamma  <code>{net.gamma:+.4f}</code>  <i>Delta 变化速度</i>")
    if net.theta is not None:
        lines.append(f"┃ Theta  <code>{net.theta:+.4f}</code>  <i>每日时间损耗</i>")
    if net.vega is not None:
        lines.append(f"┃ Vega   <code>{net.vega:+.4f}</code>  <i>波动率敏感度</i>")
    if net.rho is not None:
        lines.append(f"┃ Rho    <code>{net.rho:+.4f}</code>  <i>利率敏感度</i>")
    lines.append("┗" + "━" * 22)
    return "\n".join(lines)


def _max_quote_lag(quotes: list[LegQuote]) -> str | None:
    lags = [_lag_seconds(q.quoted_at) for q in quotes if q.quoted_at]
    if not lags:
        return None
    return _format_duration(max(lags))


def _format_lag(quoted_at: datetime) -> str:
    seconds = _lag_seconds(quoted_at)
    et = quoted_at.astimezone(ET)
    return f"报价 {et.strftime('%m-%d %H:%M')} ET · 距今 {_format_duration(seconds)}"


def _lag_seconds(quoted_at: datetime) -> int:
    now = datetime.now(timezone.utc)
    qt = quoted_at if quoted_at.tzinfo else quoted_at.replace(tzinfo=timezone.utc)
    return max(0, int((now - qt).total_seconds()))


def _format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}秒"
    if seconds < 3600:
        return f"{seconds // 60}分钟"
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    if hours < 48:
        return f"{hours}小时{mins}分" if mins else f"{hours}小时"
    days = hours // 24
    rem_h = hours % 24
    return f"{days}天{rem_h}小时" if rem_h else f"{days}天"


def _pnl_icon(pnl: float) -> str:
    if pnl > 0:
        return "📈"
    if pnl < 0:
        return "📉"
    return "➖"


def _days_to_expiry(expiry: str) -> int:
    expiry_date = date.fromisoformat(expiry)
    today = datetime.now(ET).date()
    return (expiry_date - today).days


def _money_plain(value: float) -> str:
    return f"${value:,.2f}"


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
