#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

from src.env_keys import telegram_bot_token, telegram_chat_id
from src.query_service import SpreadQueryService
from src.service import OptionsMonitorService
from src.telegram_bot import TelegramBotRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="期权价格定时查询与 Telegram 通知")
    parser.add_argument("-c", "--config", default="config.yaml")
    parser.add_argument("--once", action="store_true", help="只执行一次")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只查询并打印，不发送 Telegram",
    )
    parser.add_argument(
        "--bot",
        action="store_true",
        help="启动 Telegram 交互机器人（菜单 + 指令查询）",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("配置文件不存在: %s（可从 config.example.yaml 复制）", config_path)
        return 1

    if args.bot:
        query = SpreadQueryService.from_config_file(str(config_path))
        if not (query.config.telegram.bot_token or telegram_bot_token()):
            logger.error("未配置 TG_BOT_TOKEN")
            return 1
        TelegramBotRunner(query).run_forever()
        return 0

    service = OptionsMonitorService.from_config_file(str(config_path))
    has_tg = bool(
        (service.config.telegram.bot_token or telegram_bot_token())
        and (service.config.telegram.chat_id or telegram_chat_id())
    )
    if not args.dry_run and not has_tg:
        logger.error("未配置 Telegram：请在 .env 设置 TG_BOT_TOKEN 与 TG_CHAT_ID")
        return 1

    def job() -> None:
        try:
            service.poll_once(send_telegram=not args.dry_run and has_tg)
        except Exception:
            logger.exception("轮询失败")

    if args.once or args.dry_run:
        job()
        return 0

    scheduler = BlockingScheduler()
    scheduler.add_job(
        job,
        trigger=IntervalTrigger(seconds=service.config.interval_seconds),
        id="options_poll",
        max_instances=1,
        coalesce=True,
    )

    if service.config.notify_on_start:
        job()

    def shutdown(signum, frame) -> None:
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info("调度已启动，间隔 %d 秒", service.config.interval_seconds)
    scheduler.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
