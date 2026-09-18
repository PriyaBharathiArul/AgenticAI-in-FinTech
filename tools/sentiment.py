from __future__ import annotations

import random
import time
from typing import Any

from config import _require_dependency, yf


def _mock_handle_news_sentiment(params: dict[str, Any]) -> dict[str, Any]:
    ticker = str(params.get("tickers", "")).strip().upper()
    limit = int(params.get("limit", 5))
    articles: list[dict[str, str]] = []

    if ticker and yf is not None:
        try:
            news = yf.Ticker(ticker).news
            if news:
                for item in news[:limit]:
                    content = item.get("content", {})
                    title = content.get("title", "")
                    provider = content.get("provider", {})
                    source = provider.get("displayName", "Unknown")
                    if not title:
                        continue
                    sentiment = random.choices(
                        ["Bullish", "Somewhat-Bullish", "Neutral", "Somewhat-Bearish", "Bearish"],
                        weights=[0.15, 0.3, 0.3, 0.15, 0.1],
                        k=1,
                    )[0]
                    score_map = {
                        "Bullish": random.uniform(0.3, 0.6),
                        "Somewhat-Bullish": random.uniform(0.1, 0.35),
                        "Neutral": random.uniform(-0.1, 0.1),
                        "Somewhat-Bearish": random.uniform(-0.35, -0.1),
                        "Bearish": random.uniform(-0.6, -0.3),
                    }
                    articles.append(
                        {
                            "title": title,
                            "source": source,
                            "overall_sentiment_label": sentiment,
                            "overall_sentiment_score": str(round(score_map[sentiment], 6)),
                            "time_published": content.get(
                                "pubDate", time.strftime("%Y%m%dT%H%M%S")
                            ),
                        }
                    )
        except Exception:
            pass

    fake_headlines = [
        f"{ticker} Shows Strong Momentum Amid Market Volatility",
        f"Analysts Upgrade {ticker} Price Target Following Earnings Beat",
        f"{ticker} Faces Headwinds From Regulatory Concerns",
        f"Institutional Investors Increase Holdings in {ticker}",
        f"{ticker} Announces Strategic Partnership in AI Sector",
        f"Market Watch: {ticker} Trading Volume Surges",
        f"{ticker} Q4 Results Exceed Wall Street Expectations",
        f"Why {ticker} Could Be a Top Pick for Growth Investors",
        f"{ticker} Expands Into New Markets With Latest Acquisition",
    ]
    random.shuffle(fake_headlines)

    index = 0
    while len(articles) < limit:
        sentiment = random.choice(
            ["Bullish", "Somewhat-Bullish", "Neutral", "Somewhat-Bearish", "Bearish"]
        )
        articles.append(
            {
                "title": fake_headlines[index % len(fake_headlines)],
                "source": random.choice(
                    ["Reuters", "Bloomberg", "Yahoo Finance", "MarketWatch", "CNBC", "Seeking Alpha"]
                ),
                "overall_sentiment_label": sentiment,
                "overall_sentiment_score": str(round(random.uniform(-0.5, 0.5), 6)),
                "time_published": time.strftime("%Y%m%dT%H%M%S"),
            }
        )
        index += 1

    return {
        "items": str(len(articles[:limit])),
        "sentiment_score_definition": {},
        "feed": articles[:limit],
    }


def get_news_sentiment(ticker: str, limit: int = 5) -> dict[str, Any]:
    from tools.fundamentals import _av_get

    data = _av_get(
        {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "limit": limit,
        }
    )
    return {
        "ticker": ticker,
        "articles": [
            {
                "title": article.get("title"),
                "source": article.get("source"),
                "sentiment": article.get("overall_sentiment_label"),
                "score": article.get("overall_sentiment_score"),
            }
            for article in data.get("feed", [])[:limit]
        ],
    }
