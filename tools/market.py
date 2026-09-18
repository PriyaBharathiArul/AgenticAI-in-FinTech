from __future__ import annotations

import io
import random
import time
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

from config import (
    _is_market_open,
    _require_dependency,
    requests,
    yf,
)


def get_price_performance(tickers: list[str], period: str = "1y") -> dict[str, Any]:
    yfinance = _require_dependency(yf, "yfinance")
    results: dict[str, Any] = {}
    for ticker in tickers:
        try:
            silent_buffer = io.StringIO()
            with redirect_stdout(silent_buffer), redirect_stderr(silent_buffer):
                data = yfinance.download(
                    ticker,
                    period=period,
                    progress=False,
                    auto_adjust=True,
                    threads=False,
                )
            if data.empty:
                results[ticker] = {"error": "No data - possibly delisted"}
                continue

            start = float(data["Close"].iloc[0].item())
            end = float(data["Close"].iloc[-1].item())
            results[ticker] = {
                "start_price": round(start, 2),
                "end_price": round(end, 2),
                "pct_change": round((end - start) / start * 100, 2),
                "period": period,
            }
        except Exception as exc:
            results[ticker] = {"error": str(exc)}
    return results


def _mock_handle_market_status(_: dict[str, Any]) -> dict[str, Any]:
    us_open = _is_market_open("America/New_York", 9, 30, 16, 15)
    uk_open = _is_market_open("Europe/London", 8, 0, 16, 30)
    jp_open = _is_market_open("Asia/Tokyo", 9, 0, 15, 0)

    return {
        "endpoint": "Global Market Open & Close Status",
        "markets": [
            {
                "market_type": "Equity",
                "region": "United States",
                "primary_exchanges": "NYSE, NASDAQ, AMEX, BATS",
                "local_open": "09:30",
                "local_close": "16:15",
                "current_status": "open" if us_open else "closed",
                "notes": "",
            },
            {
                "market_type": "Equity",
                "region": "United Kingdom",
                "primary_exchanges": "London Stock Exchange",
                "local_open": "08:00",
                "local_close": "16:30",
                "current_status": "open" if uk_open else "closed",
                "notes": "",
            },
            {
                "market_type": "Equity",
                "region": "Japan",
                "primary_exchanges": "Tokyo Stock Exchange",
                "local_open": "09:00",
                "local_close": "15:00",
                "current_status": "open" if jp_open else "closed",
                "notes": "",
            },
        ],
    }


def _mock_handle_top_gainers_losers_fallback() -> dict[str, Any]:
    tickers = [
        "AAPL", "MSFT", "NVDA", "TSLA", "AMZN",
        "META", "GOOGL", "AMD", "INTC", "NFLX",
        "CRM", "ORCL", "PYPL", "SQ", "SHOP",
        "PLTR", "RIVN", "LCID", "NIO", "SOFI",
    ]

    def random_movers(n: int = 5) -> list[dict[str, str]]:
        picked = random.sample(tickers, n)
        rows = []
        for t in picked:
            price = round(random.uniform(10, 400), 2)
            change = round(random.uniform(2, 15), 2)
            rows.append(
                {
                    "ticker": t,
                    "price": str(price),
                    "change_amount": str(round(price * change / 100, 2)),
                    "change_percentage": f"{change}%",
                    "volume": str(random.randint(1_000_000, 50_000_000)),
                }
            )
        return rows

    return {
        "metadata": "Top Gainers, Losers, and Most Active (random fallback)",
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "top_gainers": random_movers(),
        "top_losers": random_movers(),
        "most_actively_traded": random_movers(),
    }


def _mock_handle_top_gainers_losers() -> dict[str, Any]:
    if requests is None:
        return _mock_handle_top_gainers_losers_fallback()

    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError:
        return _mock_handle_top_gainers_losers_fallback()

    def scrape_yahoo(url: str, n: int = 5) -> list[dict[str, str]]:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        soup = BeautifulSoup(response.text, "html.parser")
        rows = []
        for row in soup.select("table tbody tr")[:n]:
            cells = row.select("td")
            if len(cells) < 5:
                continue
            rows.append(
                {
                    "ticker": cells[0].get_text(strip=True),
                    "price": cells[3].get_text(strip=True),
                    "change_amount": cells[4].get_text(strip=True),
                    "change_percentage": cells[5].get_text(strip=True) if len(cells) > 5 else "",
                    "volume": cells[6].get_text(strip=True) if len(cells) > 6 else "",
                }
            )
        return rows

    try:
        gainers = scrape_yahoo("https://finance.yahoo.com/markets/stocks/gainers/")
        losers = scrape_yahoo("https://finance.yahoo.com/markets/stocks/losers/")
        active = scrape_yahoo("https://finance.yahoo.com/markets/stocks/most-active/")
        if not gainers and not losers and not active:
            raise ValueError("Scrape returned empty")
        return {
            "metadata": "Top Gainers, Losers, and Most Active (yahoo scrape)",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "top_gainers": gainers or [],
            "top_losers": losers or [],
            "most_actively_traded": active or [],
        }
    except Exception:
        return _mock_handle_top_gainers_losers_fallback()


def get_market_status() -> dict[str, Any]:
    from tools.fundamentals import _av_get
    return _av_get({"function": "MARKET_STATUS"})


def get_top_gainers_losers() -> dict[str, Any]:
    from tools.fundamentals import _av_get
    return _av_get({"function": "TOP_GAINERS_LOSERS"})
