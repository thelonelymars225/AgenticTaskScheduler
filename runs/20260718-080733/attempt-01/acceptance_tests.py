"""Trusted json_merge acceptance suite v1.0.0 (standard library only)."""
from __future__ import annotations

import copy
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


def test_merge_contract() -> None:
    assert callable(getattr(candidate, "merge", None)), "missing required merge(left, right)"
    left = {
        "keep": 1,
        "nested": {"left": 1, "conflict": "old"},
        "list": [1, 2, 3],
        "type_change": {"old": True},
    }
    right = {
        "added": 2,
        "nested": {"right": 2, "conflict": "new"},
        "list": [9],
        "type_change": "replacement",
    }
    left_before = copy.deepcopy(left)
    right_before = copy.deepcopy(right)
    merged = candidate.merge(left, right)
    assert merged == {
        "keep": 1,
        "added": 2,
        "nested": {"left": 1, "right": 2, "conflict": "new"},
        "list": [9],
        "type_change": "replacement",
    }
    assert left == left_before, "merge mutated its left input"
    assert right == right_before, "merge mutated its right input"
    assert candidate.merge(1, 2) == 2
    assert candidate.merge([1, 2], [3, 4, 5]) == [3, 4, 5]


def test_cli_valid_and_trailing_whitespace() -> None:
    with tempfile.TemporaryDirectory(prefix="json-merge-suite-") as directory:
        root = Path(directory)
        left_path = root / "left-input.json"
        right_path = root / "right-input.json"
        output_path = root / "result.json"
        left_path.write_text('{"z": 1, "nested": {"a": 1}}\n\t ', encoding="utf-8")
        right_path.write_text('{"a": 2, "nested": {"b": 2}}\r\n ', encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(CANDIDATE_PATH), str(left_path), str(right_path), str(output_path)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=3,
        )
        assert completed.returncode == 0, completed.stderr
        raw = output_path.read_text(encoding="utf-8")
        assert json.loads(raw) == {"a": 2, "nested": {"a": 1, "b": 2}, "z": 1}
        assert list(json.loads(raw).keys()) == ["a", "nested", "z"], "output keys are not sorted"


def test_cli_missing_and_malformed_inputs() -> None:
    with tempfile.TemporaryDirectory(prefix="json-merge-errors-") as directory:
        root = Path(directory)
        valid = root / "valid.json"
        malformed = root / "malformed.json"
        missing = root / "missing.json"
        output_path = root / "result.json"
        valid.write_text("{}", encoding="utf-8")
        malformed.write_text('{"broken":', encoding="utf-8")
        for left_path, right_path in ((missing, valid), (valid, malformed)):
            completed = subprocess.run(
                [sys.executable, str(CANDIDATE_PATH), str(left_path), str(right_path), str(output_path)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=3,
            )
            assert completed.returncode != 0
            assert completed.stderr.strip(), "CLI failure did not report to stderr"


def test_core_does_not_exit() -> None:
    try:
        candidate.merge({"a": 1}, {"a": 2})
    except SystemExit as exc:
        raise AssertionError("merge() called sys.exit") from exc
