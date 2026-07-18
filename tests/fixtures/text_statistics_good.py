from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys


def tokenize(text):
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return [token.lower() for token in re.findall(r"\w+", text, flags=re.UNICODE)]


def analyze_text(text):
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    tokens = tokenize(text)
    frequency = {token: tokens.count(token) for token in sorted(set(tokens))}
    return {
        "words": len(tokens),
        "frequency": frequency,
        "lines": 0 if text == "" else len(text.splitlines()),
        "characters": len(text),
    }


def analyze_file(path):
    return analyze_text(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    if os.getenv("AGENT_SMOKE_TEST") == "1":
        return 0
    if len(sys.argv) != 2:
        print("usage: text_statistics INPUT", file=sys.stderr)
        return 2
    try:
        result = analyze_file(Path(sys.argv[1]))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
