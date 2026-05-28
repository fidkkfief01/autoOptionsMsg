from __future__ import annotations

import logging
import time

import httpx

from src.env_keys import telegram_bot_token, telegram_chat_id
from src.query_service import SpreadQueryService

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    {"command": "start", "description": "开始使用 / 显示菜单"},
    {"command": "help", "description": "输入格式说明"},
    {"command": "query", "description": "查询期权价差示例"},
    {"command": "menu", "description": "重新显示键盘菜单"},
]

REPLY_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 查询期权"}, {"text": "❓ 帮助"}],
        [{"text": "📝 示例"}, {"text": "🔄 刷新菜单"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

HELP_TEXT = (
    "📖 <b>输入格式</b>\n\n"
    "<code>标的 +腿1, 腿2, 到期天数</code>\n\n"
    "<b>腿格式</b>\n"
    "• <code>+1 730C</code> — 买入 1 张 730 看涨\n"
    "• <code>-1 750C</code> — 卖出 1 张 750 看涨\n"
    "• <code>+2 400P</code> — 买入 2 张 400 看跌\n\n"
    "<b>到期</b>\n"
    "• <code>60天</code> / <code>60d</code> / <code>60D</code>\n\n"
    "<b>完整示例</b>\n"
    "<code>QQQ +1 730C, -1 750C, 60天</code>\n"
    "<code>+1 740C, -1 760C, 45d</code>\n\n"
    "标的可省略，默认 <code>QQQ</code>。"
)

EXAMPLE_TEXT = (
    "📝 <b>复制以下任一示例发送即可</b>\n\n"
    "<code>QQQ +1 730C, -1 750C, 60天</code>\n"
    "<code>SPY +1 580C, -1 600C, 45d</code>\n"
    "<code>+1 740C, -1 760C, 60天</code>"
)

QUERY_PROMPT = (
    "📊 <b>请发送价差指令</b>\n\n"
    "例如：\n"
    "<code>QQQ +1 730C, -1 750C, 60天</code>"
)


class TelegramBotRunner:
    def __init__(self, query_service: SpreadQueryService) -> None:
        self.query_service = query_service
        self.token = telegram_bot_token() or query_service.config.telegram.bot_token
        self.allowed_chat = str(
            telegram_chat_id() or query_service.config.telegram.chat_id
        )
        self.api = f"https://api.telegram.org/bot{self.token}"
        self._offset = 0

    def run_forever(self, poll_interval: float = 1.0) -> None:
        if not self.token:
            raise ValueError("未配置 TG_BOT_TOKEN")
        self._register_commands()
        logger.info("Telegram 机器人已启动，等待消息…")
        while True:
            try:
                self._poll_once()
            except Exception:
                logger.exception("轮询 Telegram 更新失败")
            time.sleep(poll_interval)

    def _register_commands(self) -> None:
        with httpx.Client(timeout=30.0) as client:
            client.post(
                f"{self.api}/setMyCommands",
                json={"commands": BOT_COMMANDS},
            ).raise_for_status()
        logger.info("已注册 Bot 命令列表")

    def _poll_once(self) -> None:
        with httpx.Client(timeout=35.0) as client:
            response = client.get(
                f"{self.api}/getUpdates",
                params={"offset": self._offset, "timeout": 25},
            )
            response.raise_for_status()
            updates = response.json().get("result", [])

        for update in updates:
            self._offset = update["update_id"] + 1
            message = update.get("message") or update.get("edited_message")
            if not message:
                continue
            self._handle_message(message)

    def _handle_message(self, message: dict) -> None:
        chat_id = str(message["chat"]["id"])
        if self.allowed_chat and chat_id != self.allowed_chat:
            logger.warning("忽略未授权 chat_id=%s", chat_id)
            return

        text = (message.get("text") or "").strip()
        if not text:
            return

        if text.startswith("/"):
            self._handle_command(chat_id, text)
            return

        if text in {"📊 查询期权", "查询期权"}:
            self._send_to_chat(QUERY_PROMPT, chat_id=chat_id, keyboard=REPLY_KEYBOARD)
            return
        if text in {"❓ 帮助", "帮助"}:
            self._send_to_chat(HELP_TEXT, chat_id=chat_id, keyboard=REPLY_KEYBOARD)
            return
        if text in {"📝 示例", "示例"}:
            self._send_to_chat(EXAMPLE_TEXT, chat_id=chat_id, keyboard=REPLY_KEYBOARD)
            return
        if text in {"🔄 刷新菜单", "刷新菜单"}:
            self._send_to_chat(
                "✅ 菜单已刷新，可直接发送查询指令。",
                chat_id=chat_id,
                keyboard=REPLY_KEYBOARD,
            )
            return

        if _looks_like_spread_query(text):
            reply = self.query_service.handle_command(text)
            self._send_to_chat(reply, chat_id=chat_id, keyboard=REPLY_KEYBOARD)
            return

        self._send_to_chat(
            "未识别指令。点 <b>📝 示例</b> 或发送 /help 查看格式。",
            chat_id=chat_id,
            keyboard=REPLY_KEYBOARD,
        )

    def _handle_command(self, chat_id: str, text: str) -> None:
        cmd = text.split()[0].split("@")[0].lower()
        if cmd in {"/start", "/menu"}:
            self._send_to_chat(
                "👋 <b>期权查询机器人</b>\n\n"
                "用下方按钮，或直接发送价差指令。",
                chat_id=chat_id,
                keyboard=REPLY_KEYBOARD,
            )
        elif cmd == "/help":
            self._send_to_chat(HELP_TEXT, chat_id=chat_id, keyboard=REPLY_KEYBOARD)
        elif cmd == "/query":
            self._send_to_chat(QUERY_PROMPT, chat_id=chat_id, keyboard=REPLY_KEYBOARD)
        else:
            self._send_to_chat(
                "未知命令。可用：/start /help /query /menu",
                chat_id=chat_id,
                keyboard=REPLY_KEYBOARD,
            )

    def _send_to_chat(
        self,
        text: str,
        chat_id: str | None = None,
        keyboard: dict | None = None,
    ) -> None:
        payload: dict = {
            "chat_id": chat_id or self.allowed_chat,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if keyboard:
            payload["reply_markup"] = keyboard
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{self.api}/sendMessage", json=payload)
            response.raise_for_status()


def _looks_like_spread_query(text: str) -> bool:
    import re

    return bool(re.search(r"[+-]\s*\d+\s*\d+\s*[CPcp]", text)) and bool(
        re.search(r"\d+\s*(?:天|[dD])", text, re.IGNORECASE)
    )
