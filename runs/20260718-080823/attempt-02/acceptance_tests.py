"""Trusted text_statistics acceptance suite v1.0.0 (standard library only)."""
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


def _assert_schema(result: object) -> dict[str, object]:
    assert isinstance(result, dict)
    assert set(result) == {"words", "frequency", "lines", "characters"}
    return result


def test_required_interfaces_and_type_errors() -> None:
    for name in ("tokenize", "analyze_text", "analyze_file"):
        assert callable(getattr(candidate, name, None)), f"missing required {name} interface"
    for value in (None, 7, [], {}):
        for function in (candidate.tokenize, candidate.analyze_text):
            try:
                function(value)
            except TypeError:
                pass
            except SystemExit as exc:
                raise AssertionError("library function called sys.exit") from exc
            else:
                raise AssertionError(f"{function.__name__} did not raise TypeError for {value!r}")


def test_empty_whitespace_and_line_rule() -> None:
    empty = _assert_schema(candidate.analyze_text(""))
    assert empty == {"words": 0, "frequency": {}, "lines": 0, "characters": 0}
    whitespace_text = "  \t "
    whitespace = _assert_schema(candidate.analyze_text(whitespace_text))
    assert whitespace["words"] == 0
    assert whitespace["frequency"] == {}
    assert whitespace["characters"] == len(whitespace_text)
    assert whitespace["lines"] == len(whitespace_text.splitlines())
    multiline = "one\n\nthree"
    assert candidate.analyze_text(multiline)["lines"] == 3


def test_unicode_punctuation_case_and_order() -> None:
    text = "Hello, HELLO! naïve—CAFÉ... Привет, 世界."
    expected_tokens = ["hello", "hello", "naïve", "café", "привет", "世界"]
    assert candidate.tokenize(text) == expected_tokens
    result = _assert_schema(candidate.analyze_text(text))
    assert result["words"] == len(expected_tokens)
    expected_frequency = {"café": 1, "hello": 2, "naïve": 1, "привет": 1, "世界": 1}
    assert result["frequency"] == expected_frequency
    assert list(result["frequency"].keys()) == sorted(expected_frequency)
    assert result["characters"] == len(text)
    assert result["lines"] == 1


def test_analyze_file_and_library_errors() -> None:
    with tempfile.TemporaryDirectory(prefix="text-statistics-suite-") as directory:
        root = Path(directory)
        valid = root / "input.txt"
        invalid = root / "invalid.txt"
        missing = root / "missing.txt"
        valid.write_text("One one!\nTwo", encoding="utf-8")
        invalid.write_bytes(b"\xff\xfe\xfa")
        previous = Path.cwd()
        elsewhere = root / "elsewhere"
        elsewhere.mkdir()
        try:
            os.chdir(elsewhere)
            result = _assert_schema(candidate.analyze_file(valid))
        finally:
            os.chdir(previous)
        assert result == {"words": 3, "frequency": {"one": 2, "two": 1}, "lines": 2, "characters": 12}
        for path, expected in ((missing, FileNotFoundError), (invalid, UnicodeDecodeError)):
            try:
                candidate.analyze_file(path)
            except expected:
                pass
            except SystemExit as exc:
                raise AssertionError("analyze_file called sys.exit") from exc
            else:
                raise AssertionError(f"analyze_file did not raise {expected.__name__}")


def test_cli_stable_json_and_errors() -> None:
    with tempfile.TemporaryDirectory(prefix="text-statistics-cli-") as directory:
        root = Path(directory)
        valid = root / "input.txt"
        missing = root / "missing.txt"
        valid.write_text("One one!\nTwo", encoding="utf-8")
        command = [sys.executable, str(CANDIDATE_PATH), str(valid)]
        first = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=3)
        second = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=3)
        assert first.returncode == 0, first.stderr
        assert second.returncode == 0, second.stderr
        assert first.stdout == second.stdout, "CLI JSON is not stable across identical runs"
        assert json.loads(first.stdout) == {
            "words": 3,
            "frequency": {"one": 2, "two": 1},
            "lines": 2,
            "characters": 12,
        }
        failed = subprocess.run(
            [sys.executable, str(CANDIDATE_PATH), str(missing)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=3,
        )
        assert failed.returncode != 0
        assert failed.stderr.strip(), "CLI failure did not report to stderr"
