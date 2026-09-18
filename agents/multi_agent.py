from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from agents.base import (
    AgentResult,
    calibrate_agent_result,
    run_specialist_agent,
)
from tools.schemas import (
    SCHEMA_MOVERS,
    SCHEMA_NEWS,
    SCHEMA_OVERVIEW,
    SCHEMA_PRICE,
    SCHEMA_SQL,
    SCHEMA_STATUS,
    SCHEMA_TICKERS,
)

MARKET_TOOLS = [SCHEMA_TICKERS, SCHEMA_PRICE, SCHEMA_STATUS, SCHEMA_MOVERS]
FUNDAMENTALS_TOOLS = [SCHEMA_OVERVIEW, SCHEMA_SQL, SCHEMA_TICKERS]
SENTIMENT_TOOLS = [SCHEMA_NEWS, SCHEMA_SQL, SCHEMA_TICKERS]


MARKET_AGENT_PROMPT = """
You are the Market Agent in a finance multi-agent system.

Your role is to handle only market-related reasoning:
- stock price performance over time
- sector membership
- top gainers / losers
- market open / closed status
- ranking stocks by returns

You must use tools for all factual claims.

If the question involves best / worst / top / ranking stocks or performance over time,
you must:
1. Identify candidate stocks using database tools.
2. Call get_price_performance on those tickers.
3. Rank the stocks numerically based on pct_change.
4. Return the matching stocks with ticker and return percent.

OUTPUT FORMAT
You must return valid JSON:
{
  "output": "...",
  "reason": "...",
  "confidence": 0.00
}
""".strip()


FUNDAMENTALS_AGENT_PROMPT = """
You are the Fundamentals Agent in a finance multi-agent system.

Your job:
- answer only questions related to valuation and company fundamentals
- use get_company_overview for fundamentals
- use query_local_db only for lookups and filtering
- do not invent numbers

OUTPUT FORMAT
You must return valid JSON:
{
  "output": "...",
  "reason": "...",
  "confidence": 0.00
}
""".strip()


SENTIMENT_AGENT_PROMPT = """
You are the Sentiment Agent in a finance multi-agent system.

Your job:
- answer only questions related to recent news sentiment
- use get_news_sentiment when a ticker is known
- if the question is not about sentiment/news, say so briefly instead of guessing
- do not infer sentiment without tool evidence

OUTPUT FORMAT
You must return valid JSON:
{
  "output": "...",
  "reason": "...",
  "confidence": 0.00
}
""".strip()


AGGREGATOR_PROMPT = """
You are the Aggregator in a finance multi-agent system.

You will receive the user's original question plus outputs from:
- Market Agent
- Fundamentals Agent
- Sentiment Agent

Write one final user-facing answer using only supported specialist claims. If a
specialist had tool errors or missing data, mention that uncertainty briefly.

OUTPUT FORMAT
You must return valid JSON:
{
  "output": "...",
  "reason": "...",
  "confidence": 0.00
}
""".strip()


def run_market_agent(question: str, verbose: bool = True) -> AgentResult:
    return calibrate_agent_result(
        run_specialist_agent(
            agent_name="Market Agent",
            system_prompt=MARKET_AGENT_PROMPT,
            task=question,
            tool_schemas=MARKET_TOOLS,
            max_iters=8,
            verbose=verbose,
        )
    )


def run_fundamentals_agent(question: str, verbose: bool = True) -> AgentResult:
    return calibrate_agent_result(
        run_specialist_agent(
            agent_name="Fundamentals Agent",
            system_prompt=FUNDAMENTALS_AGENT_PROMPT,
            task=question,
            tool_schemas=FUNDAMENTALS_TOOLS,
            max_iters=8,
            verbose=verbose,
        )
    )


def run_sentiment_agent(question: str, verbose: bool = True) -> AgentResult:
    return calibrate_agent_result(
        run_specialist_agent(
            agent_name="Sentiment Agent",
            system_prompt=SENTIMENT_AGENT_PROMPT,
            task=question,
            tool_schemas=SENTIMENT_TOOLS,
            max_iters=8,
            verbose=verbose,
        )
    )


def build_aggregator_input(question: str, specialist_results: dict[str, AgentResult]) -> str:
    payload: dict[str, Any] = {"user_question": question, "specialists": {}}
    for name, result in specialist_results.items():
        payload["specialists"][name] = {
            "agent_name": result.agent_name,
            "answer": result.answer,
            "tools_called": result.tools_called,
            "confidence": result.confidence,
            "issues_found": result.issues_found,
            "reasoning": result.reasoning,
            "raw_data": result.raw_data,
        }
    return json.dumps(payload, indent=2)


def run_multi_agent(question: str, verbose: bool = True) -> dict[str, Any]:
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            "market": executor.submit(run_market_agent, question, verbose),
            "fundamentals": executor.submit(run_fundamentals_agent, question, verbose),
            "sentiment": executor.submit(run_sentiment_agent, question, verbose),
        }
        specialist_results = {name: future.result() for name, future in futures.items()}

    aggregator_result = run_specialist_agent(
        agent_name="Aggregator",
        system_prompt=AGGREGATOR_PROMPT,
        task=build_aggregator_input(question, specialist_results),
        tool_schemas=[],
        max_iters=3,
        verbose=verbose,
    )

    return {
        "final_answer": aggregator_result.answer,
        "agent_results": [
            specialist_results["market"],
            specialist_results["fundamentals"],
            specialist_results["sentiment"],
            aggregator_result,
        ],
        "elapsed_sec": time.time() - start_time,
        "architecture": "parallel_specialists_aggregator",
    }
