from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


CANDIDATE_PATH = Path(os.environ["CANDIDATE_PATH"]).resolve()
spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(candidate)


def test_summarize_and_empty_input() -> None:
    lines = [
        "2026-07-18T00:00:00Z INFO started",
        "2026-07-18T00:00:01Z ERROR failed",
        "2026-07-18T00:00:02Z INFO recovered",
    ]
    assert candidate.summarize(lines) == {"ERROR": 1, "INFO": 2}
    assert candidate.summarize([]) == {}


def test_cli_reads_utf8_and_emits_stable_json() -> None:
    with tempfile.TemporaryDirectory(prefix="log-summary-regression-") as directory:
        root = Path(directory)
        source = root / "events.log"
        source.write_text(
            "2026-07-18T00:00:00Z INFO café\n2026-07-18T00:00:01Z ERROR failed\n",
            encoding="utf-8",
        )
        command = [sys.executable, str(CANDIDATE_PATH), str(source)]
        first = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=3)
        second = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=3)
        assert first.returncode == 0, first.stderr
        assert first.stdout == second.stdout
        assert json.loads(first.stdout) == {"ERROR": 1, "INFO": 1}
