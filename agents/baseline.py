from __future__ import annotations

from agents.base import AgentResult, run_specialist_agent

baseline_prompt = """
You are tasked with answering a query from a user.

OUTPUT FORMAT
You must return valid JSON:
{
  "output": "...",
  "reason": "...",
  "confidence": 0.00
}

The "output" field should contain the answer for the end user. Do not use markdown
code fences around the JSON.
""".strip()


def run_baseline(question: str, verbose: bool = True) -> AgentResult:
    return run_specialist_agent(
        agent_name="Baseline",
        system_prompt=baseline_prompt,
        task=question,
        tool_schemas=[],
        max_iters=3,
        verbose=verbose,
    )
