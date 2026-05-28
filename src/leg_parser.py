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
    target_dte: int
    legs: list[OptionLeg]


class LegParseError(ValueError):
    pass


def parse_spread_command(text: str, default_underlying: str = "QQQ") -> ParsedSpreadQuery:
    cleaned = text.strip()
    for prefix in ("结果", "查询", "query", "spread"):
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix) :].strip(" ：:，,")

    underlying = _parse_underlying(cleaned) or default_underlying.upper()
    dte_match = _DTE_PATTERN.search(cleaned)
    if not dte_match:
        raise LegParseError("缺少到期天数，例如：60天 或 60d")

    target_dte = int(dte_match.group("dte"))
    if target_dte < 1 or target_dte > 900:
        raise LegParseError("到期天数应在 1～900 之间")

    leg_matches = list(_LEG_PATTERN.finditer(cleaned))
    if len(leg_matches) < 1:
        raise LegParseError(
            "未识别到期权腿，格式示例：+1 730C, -1 750C, 60天"
        )

    legs: list[OptionLeg] = []
    for match in leg_matches:
        sign = match.group("sign")
        qty = int(match.group("qty"))
        strike = float(match.group("strike"))
        cp = match.group("cp").upper()
        legs.append(
            OptionLeg(
                underlying=underlying,
                expiry="1970-01-01",
                strike=strike,
                option_type=OptionType.CALL if cp == "C" else OptionType.PUT,
                side=Side.LONG if sign == "+" else Side.SHORT,
                quantity=qty,
                entry_price=0.0,
            )
        )

    return ParsedSpreadQuery(
        underlying=underlying,
        target_dte=target_dte,
        legs=legs,
    )


def _parse_underlying(text: str) -> str | None:
    head = text.split(",")[0].strip()
    match = _UNDERLYING_PATTERN.match(head)
    if not match:
        return None
    token = match.group(1).upper()
    if token in {"C", "P"} or _LEG_PATTERN.search(token):
        return None
    if re.fullmatch(r"[+-]?\d+", token):
        return None
    return token
