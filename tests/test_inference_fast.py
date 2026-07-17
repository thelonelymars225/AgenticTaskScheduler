"""Tests for deterministic fast-pipeline helpers; no model calls are made."""

from __future__ import annotations

import sys
import types
import unittest

fake_ollama = types.ModuleType("ollama")
fake_ollama.Client = lambda: object()
sys.modules.setdefault("ollama", fake_ollama)

fake_timer = types.ModuleType("timer")


class _Timer:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    @classmethod
    def reset_all(cls):
        pass

    @classmethod
    def print_stats(cls):
        pass


fake_timer.Timer = _Timer
sys.modules.setdefault("timer", fake_timer)

from inference.inferenceFast import (  # noqa: E402
    CHAR_LIMITS,
    _parse_plan_payload,
    _parse_review_payload,
    _strip_code_blocks,
    runtime_check,
    validate_syntax,
)


class PipelineHelperTests(unittest.TestCase):
    def test_plan_parser_uses_structured_values(self) -> None:
        plan = _parse_plan_payload(
            '{"specification":["A"],"implementation_plan":["B"],'
            '"acceptance_tests":["C"],"complexity":"simple"}'
        )
        self.assertEqual(plan.specification, ["A"])
        self.assertEqual(plan.char_limit, CHAR_LIMITS["simple"])

    def test_plan_parser_falls_back_on_invalid_json(self) -> None:
        plan = _parse_plan_payload("plain requirements")
        self.assertTrue(plan.specification)
        self.assertEqual(plan.complexity, "medium")

    def test_review_parser_fails_closed(self) -> None:
        review = _parse_review_payload("not json")
        self.assertFalse(review.passed)
        self.assertTrue(review.issues)

    def test_review_parser_requires_empty_issue_list(self) -> None:
        review = _parse_review_payload('{"verdict":"PASS","issues":["still broken"]}')
        self.assertFalse(review.passed)

    def test_code_block_extraction(self) -> None:
        self.assertEqual(_strip_code_blocks("```python\nprint('ok')\n```"), "print('ok')")

    def test_syntax_validation(self) -> None:
        self.assertEqual(validate_syntax("value = 1"), "")
        self.assertIn("SyntaxError", validate_syntax("if:"))

    def test_runtime_check_accepts_clean_exit(self) -> None:
        result = runtime_check('print("ok")', startup_grace=1.0)
        self.assertTrue(result.passed)

    def test_runtime_check_reports_crash(self) -> None:
        result = runtime_check('raise RuntimeError("broken")', startup_grace=1.0)
        self.assertFalse(result.passed)
        self.assertIn("Runtime failure", result.failures[0])


if __name__ == "__main__":
    unittest.main()
