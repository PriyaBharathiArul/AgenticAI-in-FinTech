from __future__ import annotations

import os
from typing import Any

from config import (
    ALPHAVANTAGE_API_KEY,
    AV_BASE,
    _get_info,
    _require_dependency,
    requests,
    yf,
)


def _av_get(params: dict[str, Any]) -> dict[str, Any]:
    function = params.get("function", "")
    symbol = params.get("symbol", params.get("tickers", ""))

    if requests is not None:
        query = dict(params)
        if ALPHAVANTAGE_API_KEY:
            query["apikey"] = ALPHAVANTAGE_API_KEY
        try:
            response = requests.get(f"{AV_BASE}/query", params=query, timeout=3)
            response.raise_for_status()
            return response.json()
        except Exception:
            pass

    if function == "OVERVIEW":
        return _mock_handle_overview({"symbol": symbol})
    if function == "MARKET_STATUS":
        from tools.market import _mock_handle_market_status
        return _mock_handle_market_status({})
    if function == "TOP_GAINERS_LOSERS":
        from tools.market import _mock_handle_top_gainers_losers
        return _mock_handle_top_gainers_losers()
    if function == "NEWS_SENTIMENT":
        from tools.sentiment import _mock_handle_news_sentiment
        return _mock_handle_news_sentiment(
            {"tickers": symbol, "limit": params.get("limit", 5)}
        )

    return {"error": f"Unknown function: {function}"}


def _mock_handle_overview(params: dict[str, Any]) -> dict[str, Any]:
    ticker = str(params.get("symbol", "")).strip().upper()
    if not ticker:
        return {}

    try:
        info = _get_info(ticker)
    except ModuleNotFoundError as exc:
        return {"error": str(exc)}

    if info and info.get("shortName"):
        def safe(value: Any) -> str:
            return "None" if value is None else str(value)

        pe_ratio = info.get("trailingPE") or info.get("forwardPE")
        eps = info.get("trailingEps") or info.get("forwardEps")
        return {
            "Symbol": ticker,
            "Name": info.get("shortName", ticker),
            "Sector": info.get("sector", "N/A"),
            "Industry": info.get("industry", "N/A"),
            "MarketCapitalization": safe(info.get("marketCap")),
            "PERatio": safe(pe_ratio),
            "EPS": safe(eps),
            "52WeekHigh": safe(info.get("fiftyTwoWeekHigh")),
            "52WeekLow": safe(info.get("fiftyTwoWeekLow")),
            "DividendYield": safe(info.get("dividendYield")),
            "Beta": safe(info.get("beta")),
        }
    return {}


def get_company_overview(ticker: str) -> dict[str, Any]:
    try:
        response = _av_get({"function": "OVERVIEW", "symbol": ticker})
    except Exception as exc:
        return {"error": str(exc)}

    if "Name" not in response:
        return {"error": f"No overview data for {ticker}"}

    return {
        "ticker": ticker,
        "name": response.get("Name"),
        "sector": response.get("Sector"),
        "pe_ratio": response.get("PERatio"),
        "eps": response.get("EPS"),
        "market_cap": response.get("MarketCapitalization"),
        "52w_high": response.get("52WeekHigh"),
        "52w_low": response.get("52WeekLow"),
    }
