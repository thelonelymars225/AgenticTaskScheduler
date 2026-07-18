"""Optional DeepSeek API escalation for hard, already-measured candidates.

This module is deliberately not part of planning, default generation, QA, or
acceptance.  It is a bounded last-mile repair role.  A missing key or an API
failure always falls back to the local pipeline.
"""

from __future__ import annotations

import os
import re
from typing import Any, Callable

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is present in the runtime
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency is present in the runtime
    OpenAI = None  # type: ignore[assignment,misc]


_CLIENT: Any = None


def _strip_code_blocks(text: str) -> str:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text or "", re.DOTALL | re.IGNORECASE)
    return max(blocks, key=len).strip() if blocks else (text or "").strip()


def _client() -> Any:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    if load_dotenv is not None:
        load_dotenv()
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key or OpenAI is None:
        return None
    _CLIENT = OpenAI(api_key=key, base_url="https://api.deepseek.com/v1")
    return _CLIENT


def available() -> bool:
    """Return whether a DeepSeek key is configured, without making a request."""
    if load_dotenv is not None:
        load_dotenv()
    return bool(os.environ.get("DEEPSEEK_API_KEY", "").strip()) and OpenAI is not None


def repair_code(
    code: str,
    task_markdown: str,
    failures: list[str],
    *,
    model: str = "deepseek-chat",
    record_call: Callable[[dict[str, Any]], None] | None = None,
) -> str | None:
    """Ask DeepSeek for one complete repair; return ``None`` on any failure."""
    client = _client()
    if client is None:
        return None
    failure_text = "\n".join(f"- {item[:1200]}" for item in failures[-8:] if item)
    messages = [
        {
            "role": "system",
            "content": (
                "Return only complete executable Python source. You are a bounded repair specialist. "
                "Fix the measured failures against the supplied task contract. Make the smallest coherent change; "
                "do not weaken tests, invent expectations, copy an oracle implementation, or remove required behavior. "
                "Preserve AGENT_SMOKE_TEST=1 as a safe non-blocking liveness path."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{task_markdown}\n\nMeasured failures:\n{failure_text}\n\n"
                f"Current candidate:\n```python\n{code}\n```\n\nReturn the complete corrected Python file."
            ),
        },
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.05,
        )
        usage = getattr(response, "usage", None)
        if record_call is not None:
            record_call(
                {
                    "model": f"deepseek-api:{model}",
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "output_tokens": getattr(usage, "completion_tokens", None),
                }
            )
        content = response.choices[0].message.content if response.choices else ""
        repaired = _strip_code_blocks(content)
        return repaired or None
    except Exception:
        if record_call is not None:
            record_call({"model": f"deepseek-api:{model}", "error": "request_failed"})
        return None
