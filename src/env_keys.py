from __future__ import annotations

import os


def alpaca_api_key() -> str:
    return (
        os.getenv("ALPACA_API_KEY")
        or os.getenv("Key")
        or os.getenv("APCA_API_KEY_ID")
        or ""
    ).strip()


def alpaca_secret_key() -> str:
    return (
        os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("Secret")
        or os.getenv("APCA_API_SECRET_KEY")
        or ""
    ).strip()


def telegram_bot_token() -> str:
    return os.getenv("TG_BOT_TOKEN", "").strip()


def telegram_chat_id() -> str:
    return os.getenv("TG_CHAT_ID", "").strip()
