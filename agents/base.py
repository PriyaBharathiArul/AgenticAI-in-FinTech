from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any

from config import ACTIVE_MODEL, get_openai_client
from tools import ALL_TOOL_FUNCTIONS


@dataclass
class AgentResult:
    agent_name: str
    answer: str
    tools_called: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    issues_found: list[str] = field(default_factory=list)
    reasoning: str = ""

    def summary(self) -> None:
        print(f"\n{'-' * 54}")
        print(f"Agent      : {self.agent_name}")
        print(f"Tools used : {', '.join(self.tools_called) or 'none'}")
        print(f"Confidence : {self.confidence:.0%}")
        if self.issues_found:
            print(f"Issues     : {'; '.join(self.issues_found)}")
        print(f"Answer     :\n{textwrap.indent(self.answer[:500], '  ')}")


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _parse_json_response(text: str | None) -> dict[str, Any] | None:
    if not text or not text.strip():
        return None

    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None


def _tool_call_dict(tool_call: Any) -> dict[str, Any]:
    return {
        "id": tool_call.id,
        "type": "function",
        "function": {
            "name": tool_call.function.name,
            "arguments": tool_call.function.arguments or "{}",
        },
    }


def run_specialist_agent(
    agent_name: str,
    system_prompt: str,
    task: str,
    tool_schemas: list[dict[str, Any]],
    max_iters: int = 8,
    verbose: bool = True,
) -> AgentResult:
    import config

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    tools_called: list[str] = []
    raw_data: dict[str, Any] = {}
    client = get_openai_client()

    for _ in range(max_iters):
        request: dict[str, Any] = {"model": config.ACTIVE_MODEL, "messages": messages}
        if tool_schemas:
            request["tools"] = tool_schemas
            request["tool_choice"] = "auto"

        response = client.chat.completions.create(**request)
        message = response.choices[0].message

        if getattr(message, "tool_calls", None):
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [_tool_call_dict(tc) for tc in message.tool_calls],
                }
            )

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    tool_args = {}

                if verbose:
                    print(f"[{agent_name}] calling tool: {tool_name}({tool_args})")

                tools_called.append(tool_name)

                try:
                    tool_fn = ALL_TOOL_FUNCTIONS[tool_name]
                    tool_output = tool_fn(**tool_args)
                except Exception as exc:
                    tool_output = {"error": str(exc)}

                raw_data[f"{tool_name}_{len(tools_called)}"] = tool_output
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_output),
                    }
                )
            continue

        parsed = _parse_json_response(message.content)
        if parsed:
            final_answer = str(parsed.get("output", "")).strip() or "No answer produced."
            confidence = float(parsed.get("confidence", 0.0) or 0.0)
            reasoning = str(parsed.get("reason", "")).strip()
        else:
            final_answer = (message.content or "").strip() or "No answer produced."
            confidence = 0.0
            reasoning = ""
            if verbose:
                print(f"[{agent_name}] answer was not valid JSON; using raw text.")

        return AgentResult(
            agent_name=agent_name,
            answer=final_answer,
            tools_called=tools_called,
            raw_data=raw_data,
            confidence=confidence,
            issues_found=[],
            reasoning=reasoning,
        )

    return AgentResult(
        agent_name=agent_name,
        answer="Stopped after reaching the maximum number of tool iterations.",
        tools_called=tools_called,
        raw_data=raw_data,
        confidence=0.0,
        issues_found=["max_iters_reached"],
        reasoning="",
    )


def calibrate_agent_result(result: AgentResult) -> AgentResult:
    issues = list(result.issues_found) if result.issues_found else []

    for key, value in result.raw_data.items():
        if isinstance(value, dict):
            if "error" in value:
                issues.append(f"{key}: {value['error']}")
            elif not value:
                issues.append(f"{key}: empty_result")
            elif isinstance(value.get("stocks"), list) and not value["stocks"]:
                issues.append(f"{key}: no_stocks_found")
        elif isinstance(value, list) and not value:
            issues.append(f"{key}: empty_list")

    confidence = result.confidence if isinstance(result.confidence, (int, float)) else 0.0
    if issues:
        confidence = max(0.20, confidence - 0.20)
    if not result.tools_called:
        confidence = min(confidence, 0.60)

    result.issues_found = issues
    result.confidence = float(confidence)
    return result
