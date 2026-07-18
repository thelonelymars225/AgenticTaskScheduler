"""Bounded DeepSeek API roles for candidate generation and repair.

The API is used for coding only. Planning, review, and acceptance remain
local/deterministic. A missing key or API failure falls back to the local
coding model.
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


def generate_code(
    prompt: str,
    task_markdown: str,
    *,
    model: str = "deepseek-chat",
    record_call: Callable[[dict[str, Any]], None] | None = None,
) -> str | None:
    """Generate a complete candidate through the DeepSeek coding API."""
    client = _client()
    if client is None:
        return None
    messages = [
        {
            "role": "system",
            "content": (
                "Return only complete executable Python source. Implement the supplied contract exactly. "
                "Build the smallest reliable solution, handle explicit edge cases, and keep the source below the "
                "requested limit. When AGENT_SMOKE_TEST=1, exit 0 after a safe liveness probe. Do not put behavioral "
                "assertions or hand-calculated expected outputs in the smoke path."
            ),
        },
        {"role": "user", "content": f"Request:\n{prompt}\n\n{task_markdown}\n\nReturn the complete Python file."},
    ]
    try:
        response = client.chat.completions.create(model=model, messages=messages, temperature=0.1)
        usage = getattr(response, "usage", None)
        if record_call is not None:
            record_call({
                "model": f"deepseek-api:{model}",
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "output_tokens": getattr(usage, "completion_tokens", None),
            })
        content = response.choices[0].message.content if response.choices else ""
        generated = _strip_code_blocks(content)
        return generated or None
    except Exception:
        if record_call is not None:
            record_call({"model": f"deepseek-api:{model}", "error": "request_failed"})
        return None
