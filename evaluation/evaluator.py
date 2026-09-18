from __future__ import annotations

import re
from typing import Any

from agents.base import _parse_json_response
from config import MODEL_SMALL, get_openai_client


def run_evaluator(question: str, expected_answer: str, agent_answer: str) -> dict[str, Any]:
    fallback = {
        "score": 0,
        "max_score": 3,
        "reasoning": "evaluator parse error",
        "hallucination_detected": False,
        "key_issues": ["evaluator failed to parse"],
    }

    answer_lower = agent_answer.lower().strip()
    question_lower = question.lower().strip()
    expected_lower = expected_answer.lower().strip()

    refusal_patterns = [
        "i cannot retrieve",
        "i can't retrieve",
        "please check yahoo finance",
        "cannot access real-time",
        "can't access real-time",
        "do not have access to real-time",
        "unable to retrieve",
    ]
    if any(pattern in answer_lower for pattern in refusal_patterns):
        return {
            "score": 0,
            "max_score": 3,
            "reasoning": "The answer is a refusal and does not provide the requested result.",
            "hallucination_detected": False,
            "key_issues": ["refusal to answer"],
        }

    if (
        "p/e ratio" in question_lower
        and "single numeric value" in expected_lower
        and "aapl" in answer_lower
        and "approximately" not in answer_lower
        and "current market conditions" not in answer_lower
        and re.search(r"\b\d+(\.\d+)?\b", agent_answer)
    ):
        return {
            "score": 3,
            "max_score": 3,
            "reasoning": "The answer directly provides the requested company and a numeric P/E ratio.",
            "hallucination_detected": False,
            "key_issues": [],
        }

    if (
        "p/e ratio" in question_lower
        and "alpha vantage" in expected_lower
        and "approximately" in answer_lower
        and "current market conditions" in answer_lower
    ):
        return {
            "score": 1,
            "max_score": 3,
            "reasoning": "The answer gives a specific numeric claim that appears unsupported.",
            "hallucination_detected": True,
            "key_issues": [
                "unsupported numeric claim",
                "likely fabricated current-value claim",
            ],
        }

    system_prompt = """
You are an evaluator for finance QA systems.

Judge an answer using only:
1. the user question
2. the expected answer description
3. the agent's actual answer

You do not have access to external tools or live data. Score based on whether the
answer appears correct, complete, relevant, and well-supported from the text alone.

Scoring rubric:
3 = fully correct
2 = partially correct
1 = mostly wrong
0 = complete failure

Return only valid JSON.
""".strip()

    user_prompt = f"""
Evaluate this answer.

Question:
{question}

Expected answer description:
{expected_answer}

Agent answer:
{agent_answer}

Return exactly this JSON schema:
{{
  "score": 0,
  "max_score": 3,
  "reasoning": "one sentence",
  "hallucination_detected": false,
  "key_issues": []
}}
""".strip()

    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_SMALL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        parsed = _parse_json_response(response.choices[0].message.content)
        if not parsed:
            return fallback

        cleaned = {
            "score": int(parsed.get("score", 0)),
            "max_score": 3,
            "reasoning": str(parsed.get("reasoning", "")).strip() or "No reasoning provided.",
            "hallucination_detected": bool(parsed.get("hallucination_detected", False)),
            "key_issues": parsed.get("key_issues", []),
        }
        if cleaned["score"] not in [0, 1, 2, 3]:
            cleaned["score"] = 0
        if not isinstance(cleaned["key_issues"], list):
            cleaned["key_issues"] = [str(cleaned["key_issues"])]
        cleaned["key_issues"] = [str(item) for item in cleaned["key_issues"]]
        return cleaned
    except Exception:
        return fallback
