from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    import yfinance as yf
except ModuleNotFoundError:
    yf = None

try:
    import requests
except ModuleNotFoundError:
    requests = None

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "stocks.db"
AV_BASE = os.getenv("AV_BASE", "http://localhost:2345")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ALPHAVANTAGE_API_KEY = (
    os.getenv("ALPHAVANTAGE_API_KEY")
    or os.getenv("ALPHA_VANTAGE")
    or ""
)

MODEL_SMALL = "gpt-4o-mini"
MODEL_LARGE = "gpt-4o"
ACTIVE_MODEL = MODEL_SMALL

_client: OpenAI | None = None
_info_cache: dict[str, Any] = {}


def _require_dependency(module: Any, package_name: str) -> Any:
    if module is None:
        raise ModuleNotFoundError(
            f"{package_name} is required for this operation. "
            f"Install it with `pip install {package_name}`."
        )
    return module


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        openai_cls = _require_dependency(OpenAI, "openai")
        api_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export it before running agent functions."
            )
        _client = openai_cls(api_key=api_key)
    return _client


def set_active_model(model: str) -> None:
    global ACTIVE_MODEL
    ACTIVE_MODEL = model


def _resolve_path(path: str | os.PathLike[str]) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT_DIR / path_obj


def _get_info(ticker: str) -> dict[str, Any] | None:
    yfinance = _require_dependency(yf, "yfinance")
    if ticker not in _info_cache:
        try:
            _info_cache[ticker] = yfinance.Ticker(ticker).info
        except Exception:
            _info_cache[ticker] = None
    return _info_cache[ticker]


def _is_market_open(
    tz_name: str,
    open_hour: int,
    open_minute: int,
    close_hour: int,
    close_minute: int,
) -> bool:
    now = datetime.now(ZoneInfo(tz_name))
    if now.weekday() >= 5:
        return False
    current_minutes = now.hour * 60 + now.minute
    return (open_hour * 60 + open_minute) <= current_minutes < (
        close_hour * 60 + close_minute
    )
