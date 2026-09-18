from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from config import ACTIVE_MODEL, _require_dependency, _resolve_path

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

BENCHMARK_QUESTIONS = [
    {
        "id": "Q01",
        "complexity": "easy",
        "category": "sector_lookup",
        "question": "List all semiconductor companies in the database.",
        "expected": "Should return company names and tickers for semiconductor stocks from the local DB.",
    },
    {
        "id": "Q02",
        "complexity": "easy",
        "category": "market_status",
        "question": "Are the US stock markets open right now?",
        "expected": "Should return the current open/closed status for NYSE and NASDAQ with trading hours.",
    },
    {
        "id": "Q03",
        "complexity": "easy",
        "category": "fundamentals",
        "question": "What is the P/E ratio of Apple (AAPL)?",
        "expected": "Should return AAPL P/E ratio as a single numeric value fetched from Alpha Vantage.",
    },
    {
        "id": "Q04",
        "complexity": "easy",
        "category": "sentiment",
        "question": "What is the latest news sentiment for Microsoft (MSFT)?",
        "expected": "Should return 3-5 recent MSFT headlines with sentiment labels and scores.",
    },
    {
        "id": "Q05",
        "complexity": "easy",
        "category": "price",
        "question": "What is NVIDIA's stock price performance over the last month?",
        "expected": "Should return NVDA start price, end price, and percent change for 1 month.",
    },
    {
        "id": "Q06",
        "complexity": "medium",
        "category": "price_comparison",
        "question": "Compare the 1-year price performance of AAPL, MSFT, and GOOGL. Which grew the most?",
        "expected": "Should fetch 1-year performance for all three tickers and identify the best performer.",
    },
    {
        "id": "Q07",
        "complexity": "medium",
        "category": "fundamentals",
        "question": "Compare the P/E ratios of AAPL, MSFT, and NVDA. Which looks most expensive?",
        "expected": "Should return P/E ratios for all three tickers and identify the highest P/E.",
    },
    {
        "id": "Q08",
        "complexity": "medium",
        "category": "sector_price",
        "question": "Which energy stocks in the database had the best 6-month performance?",
        "expected": "Should query the DB for energy tickers, fetch six-month performance, and rank them.",
    },
    {
        "id": "Q09",
        "complexity": "medium",
        "category": "sentiment",
        "question": "What is the news sentiment for Tesla (TSLA) and how has its stock moved this month?",
        "expected": "Should return TSLA news sentiment and 1-month price change from two tools.",
    },
    {
        "id": "Q10",
        "complexity": "medium",
        "category": "fundamentals",
        "question": "What are the 52-week high and low for JPMorgan (JPM) and Goldman Sachs (GS)?",
        "expected": "Should return 52-week high and low for both JPM and GS.",
    },
    {
        "id": "Q11",
        "complexity": "hard",
        "category": "multi_condition",
        "question": "Which tech stocks dropped this month but grew this year? Return the top 3.",
        "expected": "Should filter for negative 1-month and positive YTD performance, then return the top three.",
    },
    {
        "id": "Q12",
        "complexity": "hard",
        "category": "multi_condition",
        "question": "Which large-cap technology stocks on NASDAQ have grown more than 20% this year?",
        "expected": "Should query large-cap NASDAQ technology stocks, fetch YTD performance, and filter for >20%.",
    },
    {
        "id": "Q13",
        "complexity": "hard",
        "category": "cross_domain",
        "question": "For the top 3 semiconductor stocks by 1-year return, what are their P/E ratios and current news sentiment?",
        "expected": "Should combine price, fundamentals, and sentiment to answer for the top three semiconductors.",
    },
    {
        "id": "Q14",
        "complexity": "hard",
        "category": "cross_domain",
        "question": "Compare the market cap, P/E ratio, and 1-year stock performance of JPM, GS, and BAC.",
        "expected": "Should return market cap, P/E, and 1-year percent change for all three tickers.",
    },
    {
        "id": "Q15",
        "complexity": "hard",
        "category": "multi_condition",
        "question": "Which finance sector stocks are trading closer to their 52-week low than their 52-week high? Return the news sentiment for each.",
        "expected": "Should identify qualifying finance stocks and then fetch news sentiment for each.",
    },
]


@dataclass
class EvalRecord:
    question_id: str
    question: str
    complexity: str
    category: str
    expected: str
    bl_answer: str = ""
    bl_time: float = 0.0
    bl_score: int = -1
    bl_reasoning: str = ""
    bl_hallucination: str = ""
    bl_issues: str = ""
    sa_answer: str = ""
    sa_tools: str = ""
    sa_tool_count: int = 0
    sa_iters: int = 0
    sa_time: float = 0.0
    sa_score: int = -1
    sa_reasoning: str = ""
    sa_hallucination: str = ""
    sa_issues: str = ""
    ma_answer: str = ""
    ma_tools: str = ""
    ma_tool_count: int = 0
    ma_time: float = 0.0
    ma_confidence: str = ""
    ma_critic_issues: int = 0
    ma_agents: str = ""
    ma_architecture: str = ""
    ma_score: int = -1
    ma_reasoning: str = ""
    ma_hallucination: str = ""
    ma_issues: str = ""


_COL_NAMES = {
    "question_id": "Question ID",
    "question": "Question",
    "complexity": "Difficulty",
    "category": "Category",
    "expected": "Expected Answer",
    "bl_answer": "Baseline Answer",
    "bl_time": "Baseline Time (s)",
    "bl_score": "Baseline Score /3",
    "bl_reasoning": "Baseline Eval Reasoning",
    "bl_hallucination": "Baseline Hallucination",
    "bl_issues": "Baseline Issues",
    "sa_answer": "SA Answer",
    "sa_tools": "SA Tools Used",
    "sa_tool_count": "SA Tool Count",
    "sa_iters": "SA Iterations",
    "sa_time": "SA Time (s)",
    "sa_score": "SA Score /3",
    "sa_reasoning": "SA Eval Reasoning",
    "sa_hallucination": "SA Hallucination",
    "sa_issues": "SA Issues",
    "ma_answer": "MA Answer",
    "ma_tools": "MA Tools Used",
    "ma_tool_count": "MA Tool Count",
    "ma_time": "MA Time (s)",
    "ma_confidence": "MA Avg Confidence",
    "ma_critic_issues": "MA Critic Issue Count",
    "ma_agents": "MA Agents Activated",
    "ma_architecture": "MA Architecture",
    "ma_score": "MA Score /3",
    "ma_reasoning": "MA Eval Reasoning",
    "ma_hallucination": "MA Hallucination",
    "ma_issues": "MA Issues",
}


def _save_excel(records: list[EvalRecord], path: str) -> None:
    pandas = _require_dependency(pd, "pandas")
    df = pandas.DataFrame([record.__dict__ for record in records]).rename(columns=_COL_NAMES)

    with pandas.ExcelWriter(_resolve_path(path), engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")

        rows = []
        for arch, score_col, time_col, hall_col in [
            ("Baseline", "Baseline Score /3", "Baseline Time (s)", "Baseline Hallucination"),
            ("Single Agent", "SA Score /3", "SA Time (s)", "SA Hallucination"),
            ("Multi Agent", "MA Score /3", "MA Time (s)", "MA Hallucination"),
        ]:
            for tier in ["easy", "medium", "hard", "all"]:
                subset = df if tier == "all" else df[df["Difficulty"] == tier]
                valid = subset[subset[score_col] >= 0]
                average_score = valid[score_col].mean() if len(valid) else 0
                rows.append(
                    {
                        "Architecture": arch,
                        "Difficulty": tier,
                        "Questions Scored": len(valid),
                        "Avg Score /3": round(average_score, 2),
                        "Accuracy %": round(average_score / 3 * 100, 1),
                        "Avg Time (s)": round(df[time_col].mean(), 1),
                        "Hallucinations": (df[hall_col] == "True").sum(),
                    }
                )
        pandas.DataFrame(rows).to_excel(writer, index=False, sheet_name="Summary")


def run_full_evaluation(
    output_xlsx: str = "evaluation/results.xlsx",
    delay_sec: float = 3.0,
) -> str:
    import config
    from agents.baseline import run_baseline
    from agents.multi_agent import run_multi_agent
    from agents.single_agent import run_single_agent
    from evaluation.evaluator import run_evaluator

    records: list[EvalRecord] = []
    total = len(BENCHMARK_QUESTIONS)

    print(f"\n{'=' * 62}")
    print(f"  FULL EVALUATION  |  {total} questions x 3 architectures")
    print(f"  Model: {config.ACTIVE_MODEL}  |  Output: {output_xlsx}")
    print(f"{'=' * 62}\n")

    for index, question in enumerate(BENCHMARK_QUESTIONS, start=1):
        print(
            f"[{index:02d}/{total}] {question['id']} "
            f"({question['complexity']:6s}) {question['question'][:52]}..."
        )
        record = EvalRecord(
            question_id=question["id"],
            question=question["question"],
            complexity=question["complexity"],
            category=question["category"],
            expected=question["expected"],
        )

        print("         baseline  ...", end=" ", flush=True)
        try:
            start = time.time()
            baseline = run_baseline(question["question"], verbose=False)
            record.bl_answer = baseline.answer.replace("\n", " ")
            record.bl_time = round(time.time() - start, 2)
            evaluation = run_evaluator(question["question"], question["expected"], baseline.answer)
            record.bl_score = evaluation.get("score", -1)
            record.bl_reasoning = evaluation.get("reasoning", "")
            record.bl_hallucination = str(evaluation.get("hallucination_detected", False))
            record.bl_issues = " | ".join(evaluation.get("key_issues", []))
            print(f"ok  {record.bl_time:5.1f}s  score {record.bl_score}/3")
        except Exception as exc:
            print(f"failed  {exc}")

        print("         single    ...", end=" ", flush=True)
        try:
            start = time.time()
            single = run_single_agent(question["question"], verbose=False)
            record.sa_answer = single.answer.replace("\n", " ")
            record.sa_tools = ", ".join(single.tools_called)
            record.sa_tool_count = len(single.tools_called)
            record.sa_iters = len(single.tools_called) + 1
            record.sa_time = round(time.time() - start, 2)
            evaluation = run_evaluator(question["question"], question["expected"], single.answer)
            record.sa_score = evaluation.get("score", -1)
            record.sa_reasoning = evaluation.get("reasoning", "")
            record.sa_hallucination = str(evaluation.get("hallucination_detected", False))
            record.sa_issues = " | ".join(evaluation.get("key_issues", []))
            print(f"ok  {record.sa_time:5.1f}s  score {record.sa_score}/3")
        except Exception as exc:
            print(f"failed  {exc}")

        print("         multi     ...", end=" ", flush=True)
        try:
            start = time.time()
            multi = run_multi_agent(question["question"], verbose=False)
            results = multi.get("agent_results", [])
            all_tools = [tool for result in results for tool in result.tools_called]
            all_issues = [issue for result in results for issue in result.issues_found]
            avg_conf = sum(result.confidence for result in results) / len(results) if results else 0.0

            record.ma_answer = multi["final_answer"].replace("\n", " ")
            record.ma_tools = ", ".join(dict.fromkeys(all_tools))
            record.ma_tool_count = len(all_tools)
            record.ma_time = round(time.time() - start, 2)
            record.ma_confidence = f"{avg_conf:.0%}"
            record.ma_critic_issues = len(all_issues)
            record.ma_agents = ", ".join(result.agent_name for result in results)
            record.ma_architecture = multi.get("architecture", "")

            evaluation = run_evaluator(question["question"], question["expected"], multi["final_answer"])
            record.ma_score = evaluation.get("score", -1)
            record.ma_reasoning = evaluation.get("reasoning", "")
            record.ma_hallucination = str(evaluation.get("hallucination_detected", False))
            record.ma_issues = " | ".join(evaluation.get("key_issues", []))
            print(f"ok  {record.ma_time:5.1f}s  score {record.ma_score}/3")
        except Exception as exc:
            print(f"failed  {exc}")

        records.append(record)
        _save_excel(records, output_xlsx)

        if index < total:
            print(f"         waiting {delay_sec}s ...\n")
            time.sleep(delay_sec)

    print(f"\n{'=' * 62}  RESULTS")
    print(f"{'Architecture':<18} {'Easy':>8} {'Medium':>8} {'Hard':>8} {'Overall':>8}")
    print("-" * 60)
    for arch, score_key in [
        ("Baseline", "bl_score"),
        ("Single Agent", "sa_score"),
        ("Multi Agent", "ma_score"),
    ]:
        def pct(tier: str, _key: str = score_key) -> str:
            scores = [
                getattr(record, _key)
                for record in records
                if getattr(record, _key) >= 0
                and (tier == "all" or record.complexity == tier)
            ]
            return f"{sum(scores) / len(scores) / 3 * 100:.0f}%" if scores else "-"

        print(f"{arch:<18} {pct('easy'):>8} {pct('medium'):>8} {pct('hard'):>8} {pct('all'):>8}")

    print(f"\nSaved results to {output_xlsx}")
    return str(_resolve_path(output_xlsx))
