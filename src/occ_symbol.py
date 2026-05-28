from __future__ import annotations

from datetime import datetime

from src.models import OptionLeg, OptionType


def leg_to_occ_symbol(leg: OptionLeg) -> str:
    root = leg.underlying.upper()
    expiry = datetime.strptime(leg.expiry, "%Y-%m-%d").strftime("%y%m%d")
    cp = "C" if leg.option_type == OptionType.CALL else "P"
    strike_code = f"{int(round(leg.strike * 1000)):08d}"
    return f"{root}{expiry}{cp}{strike_code}"
