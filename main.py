"""Cron-friendly command-line entry point."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from inference.inferenceFast import _strip_code_blocks, project_management
from timer import Timer

DEFAULT_PROMPT = "write a python game of pong using tkinter and object oriented programming"


def main() -> int:
    """Run one generation task and return a cron-friendly exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="*")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()

    prompt = " ".join(args.prompt).strip() or os.getenv("AGENT_TASK_PROMPT", DEFAULT_PROMPT)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with Timer("pipeline.total"):
        analysis, code, qa_result = project_management(prompt)

    (output_dir / "output.txt").write_text(
        f"=== Analysis ===\n{analysis}\n\n=== Code ===\n{code}\n\n=== QA Result ===\n{qa_result}\n",
        encoding="utf-8",
    )

    clean_code = _strip_code_blocks(code)
    if not clean_code:
        print("No executable code was generated")
        return 1

    output_path = output_dir / "output.py"
    output_path.write_text(clean_code, encoding="utf-8")
    print(f"Written {len(clean_code)} characters to {output_path}")
    print(qa_result)
    return 0 if qa_result.startswith("VERDICT: PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
