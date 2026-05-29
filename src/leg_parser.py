from __future__ import annotations

import re
from dataclasses import dataclass

from src.models import OptionLeg, OptionType, Side

_LEG_PATTERN = re.compile(
    r"(?P<sign>[+-])\s*(?P<qty>\d+)\s*(?P<strike>\d+(?:\.\d+)?)\s*(?P<cp>[CPcp])",
    re.IGNORECASE,
)
_DTE_PATTERN = re.compile(
    r"(?P<dte>\d+)\s*(?:天|[dD](?:ays?)?|日)\b",
    re.IGNORECASE,
)
_UNDERLYING_PATTERN = re.compile(r"^([A-Za-z]{1,6})\b")


@dataclass(frozen=True)
class ParsedSpreadQuery:
    underlying: str
    target_dte: int | None
    leg_dtes: list[int]
    legs: list[OptionLeg]


class LegParseError(ValueError):
    pass


def parse_spread_command(text: str, default_underlying: str = "QQQ") -> ParsedSpreadQuery:
    cleaned = text.strip()
    for prefix in ("结果", "查询", "query", "spread"):
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix) :].strip(" ：:，,")

    underlying = _parse_underlying(cleaned) or default_underlying.upper()
    legs: list[OptionLeg] = []
    leg_dtes: list[int | None] = []

    for part in re.split(r"[,，]", cleaned):
        segment = part.strip()
        if not segment:
            continue

        leg_match = _LEG_PATTERN.search(segment)
        dte_match = _DTE_PATTERN.search(segment)

        if leg_match:
            legs.append(_build_leg(leg_match, underlying))
            leg_dtes.append(_parse_dte(dte_match) if dte_match else None)
            continue

        if dte_match and legs and leg_dtes[-1] is None:
            leg_dtes[-1] = _parse_dte(dte_match)
            continue

    if len(legs) < 1:
        raise LegParseError(
            "未识别到期权腿，格式示例：+1 730C, -1 750C, 60天"
        )

    global_dtes = [int(m.group("dte")) for m in _DTE_PATTERN.finditer(cleaned)]
    for dte in global_dtes:
        _validate_dte(dte)

    target_dte: int | None = None
    if any(dte is None for dte in leg_dtes):
        if len(global_dtes) == 1:
            target_dte = global_dtes[0]
            leg_dtes = [target_dte for _ in legs]
        else:
            raise LegParseError(
                "每条腿都需要到期天数，例如：QQQ +1 730C,59天,-1 750C,307天"
            )

    resolved_dtes = [int(dte) for dte in leg_dtes]
    if len(set(resolved_dtes)) == 1:
        target_dte = resolved_dtes[0]

    return ParsedSpreadQuery(
        underlying=underlying,
        target_dte=target_dte,
        leg_dtes=resolved_dtes,
        legs=legs,
    )


def _build_leg(match: re.Match[str], underlying: str) -> OptionLeg:
    sign = match.group("sign")
    qty = int(match.group("qty"))
    strike = float(match.group("strike"))
    cp = match.group("cp").upper()
    return OptionLeg(
        underlying=underlying,
        expiry="1970-01-01",
        strike=strike,
        option_type=OptionType.CALL if cp == "C" else OptionType.PUT,
        side=Side.LONG if sign == "+" else Side.SHORT,
        quantity=qty,
        entry_price=0.0,
    )


def _parse_dte(match: re.Match[str] | None) -> int:
    if not match:
        raise LegParseError("缺少到期天数，例如：60天 或 60d")
    dte = int(match.group("dte"))
    _validate_dte(dte)
    return dte


def _validate_dte(dte: int) -> None:
    if dte < 1 or dte > 900:
        raise LegParseError("到期天数应在 1～900 之间")


def _parse_underlying(text: str) -> str | None:
    head = re.split(r"[,，]", text)[0].strip()
    match = _UNDERLYING_PATTERN.match(head)
    if not match:
        return None
    token = match.group(1).upper()
    if token in {"C", "P"} or _LEG_PATTERN.search(token):
        return None
    if re.fullmatch(r"[+-]?\d+", token):
        return None
    return token
