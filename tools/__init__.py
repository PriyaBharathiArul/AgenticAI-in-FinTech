from tools.database import create_local_database, get_tickers_by_sector, query_local_db
from tools.fundamentals import get_company_overview
from tools.market import get_market_status, get_price_performance, get_top_gainers_losers
from tools.schemas import ALL_SCHEMAS
from tools.sentiment import get_news_sentiment

ALL_TOOL_FUNCTIONS = {
    "get_tickers_by_sector": get_tickers_by_sector,
    "get_price_performance": get_price_performance,
    "get_company_overview": get_company_overview,
    "get_market_status": get_market_status,
    "get_top_gainers_losers": get_top_gainers_losers,
    "get_news_sentiment": get_news_sentiment,
    "query_local_db": query_local_db,
}

__all__ = [
    "ALL_SCHEMAS",
    "ALL_TOOL_FUNCTIONS",
    "create_local_database",
    "get_tickers_by_sector",
    "get_price_performance",
    "get_company_overview",
    "get_market_status",
    "get_top_gainers_losers",
    "get_news_sentiment",
    "query_local_db",
]
