from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.env_keys import alpaca_api_key, alpaca_secret_key
from src.models import AppConfig

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _expand_env(value: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), "")

    return _ENV_PATTERN.sub(replacer, value)


def _walk_expand_env(node: object) -> object:
    if isinstance(node, dict):
        return {key: _walk_expand_env(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_walk_expand_env(item) for item in node]
    if isinstance(node, str):
        return _expand_env(node)
    return node


def load_config(path: str | Path) -> AppConfig:
    load_dotenv()
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    expanded = _walk_expand_env(raw)
    config = AppConfig.model_validate(expanded)

    if config.provider == "alpaca" and (not alpaca_api_key() or not alpaca_secret_key()):
        raise ValueError("Alpaca 模式需要在 .env 中设置 Key/Secret（或 ALPACA_API_KEY/ALPACA_SECRET_KEY）")

    return config
