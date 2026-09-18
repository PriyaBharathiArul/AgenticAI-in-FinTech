from __future__ import annotations

from agents.base import AgentResult, run_specialist_agent
from tools import ALL_SCHEMAS

SINGLE_AGENT_PROMPT = """
You are tasked with answering a user question about stocks and financial data.

Decide whether to use the available tools, and if so which tools and arguments are
needed. Prefer the provided tools whenever they are relevant.

OUTPUT FORMAT
You must return valid JSON:
{
  "output": "...",
  "reason": "...",
  "confidence": 0.00
}

The "output" field should contain the final user-facing answer. Do not wrap the JSON
in markdown code fences.
""".strip()


def run_single_agent(question: str, verbose: bool = True) -> AgentResult:
    return run_specialist_agent(
        agent_name="Single Agent",
        system_prompt=SINGLE_AGENT_PROMPT,
        task=question,
        tool_schemas=ALL_SCHEMAS,
        max_iters=10,
        verbose=verbose,
    )
