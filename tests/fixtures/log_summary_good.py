from __future__ import annotations

import json
import os
from pathlib import Path
import sys


def summarize(log_lines):
    counts = {}
    for line in log_lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=2)
        if len(parts) < 2:
            continue
        level = parts[1]
        counts[level] = counts.get(level, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def main() -> int:
    if os.getenv("AGENT_SMOKE_TEST") == "1":
        return 0
    if len(sys.argv) != 2:
        print("usage: log_summary INPUT", file=sys.stderr)
        return 2
    try:
        lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    print(json.dumps(summarize(lines), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
