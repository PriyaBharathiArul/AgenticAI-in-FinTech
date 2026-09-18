from __future__ import annotations

from typing import Any


def _schema(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str],
) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


SCHEMA_TICKERS = _schema(
    "get_tickers_by_sector",
    "Return all stocks in a sector or industry from the local database. "
    "Use broad sector names ('Technology', 'Energy') or sub-sectors "
    "('semiconductor', 'insurance').",
    {"sector": {"type": "string", "description": "Sector or industry name"}},
    ["sector"],
)

SCHEMA_PRICE = _schema(
    "get_price_performance",
    "Get percent price change for a list of tickers over a time period. "
    "Periods: '1mo', '3mo', '6mo', 'ytd', '1y'.",
    {
        "tickers": {"type": "array", "items": {"type": "string"}},
        "period": {"type": "string", "default": "1y"},
    },
    ["tickers"],
)

SCHEMA_OVERVIEW = _schema(
    "get_company_overview",
    "Get fundamentals for one stock: P/E ratio, EPS, market cap, 52-week high and low.",
    {"ticker": {"type": "string", "description": "Ticker symbol such as 'AAPL'."}},
    ["ticker"],
)

SCHEMA_STATUS = _schema(
    "get_market_status",
    "Check whether global stock exchanges are currently open or closed.",
    {},
    [],
)

SCHEMA_MOVERS = _schema(
    "get_top_gainers_losers",
    "Get today's top gaining, top losing, and most actively traded stocks.",
    {},
    [],
)

SCHEMA_NEWS = _schema(
    "get_news_sentiment",
    "Get recent news headlines and Bullish/Bearish/Neutral sentiment scores for a stock.",
    {
        "ticker": {"type": "string"},
        "limit": {"type": "integer", "default": 5},
    },
    ["ticker"],
)

SCHEMA_SQL = _schema(
    "query_local_db",
    "Run a SQL SELECT query on stocks.db. "
    "Table 'stocks' columns: ticker, company, sector, industry, market_cap, exchange.",
    {"sql": {"type": "string", "description": "A valid SQL SELECT statement."}},
    ["sql"],
)

ALL_SCHEMAS = [
    SCHEMA_TICKERS,
    SCHEMA_PRICE,
    SCHEMA_OVERVIEW,
    SCHEMA_STATUS,
    SCHEMA_MOVERS,
    SCHEMA_NEWS,
    SCHEMA_SQL,
]
