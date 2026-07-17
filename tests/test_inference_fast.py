"""Tests for deterministic fast-pipeline helpers; no model calls are made."""

from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

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
    _fast_task_plan,
    analyze_task,
    PipelineResult,
    ReviewResult,
    ValidationResult,
    project_management_with_attempts,
    quality_review,
    run_acceptance_tests,
    runtime_check,
    validate_syntax,
)
from inference.pipeline_config import (  # noqa: E402
    ENABLE_ACCEPTANCE_TESTS,
    ENABLE_LLM_REVIEW,
    ENABLE_PLANNING,
    MAX_REPAIRS,
)


class PipelineHelperTests(unittest.TestCase):
    def test_default_profile_prioritizes_quality(self) -> None:
        self.assertTrue(ENABLE_PLANNING)
        self.assertTrue(ENABLE_LLM_REVIEW)
        self.assertEqual(MAX_REPAIRS, 2)
        self.assertTrue(ENABLE_ACCEPTANCE_TESTS)

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

    def test_plan_parser_rejects_nested_fields(self) -> None:
        plan = _parse_plan_payload('{"specification":{"nested":"value"}}')
        self.assertEqual(plan.specification, ["Implement the user request."])

    @patch("inference.inferenceFast._chat", return_value="")
    def test_planner_fallback_keeps_original_request_for_qa(self, mock_chat) -> None:
        plan = analyze_task("build a JSON validator with range checks")
        self.assertEqual(plan.specification, ["build a JSON validator with range checks"])

    def test_fast_plan_needs_no_model_and_preserves_request(self) -> None:
        plan = _fast_task_plan("build a small CLI")
        self.assertEqual(plan.specification, ["build a small CLI"])
        self.assertTrue(plan.acceptance_tests)

    def test_review_parser_fails_closed(self) -> None:
        review = _parse_review_payload("not json")
        self.assertFalse(review.passed)
        self.assertTrue(review.issues)

    def test_review_parser_requires_empty_issue_list(self) -> None:
        review = _parse_review_payload('{"verdict":"PASS","issues":["still broken"]}')
        self.assertFalse(review.passed)

    @patch("inference.inferenceFast._chat", side_effect=["", '{"verdict":"PASS","issues":[]}'])
    def test_quality_review_retries_empty_response(self, mock_chat) -> None:
        review = quality_review("print('ok')", _fast_task_plan("print ok"))
        self.assertTrue(review.passed)
        self.assertEqual(mock_chat.call_count, 2)

    @patch("inference.inferenceFast._chat", return_value="")
    def test_quality_review_reports_unavailable_after_retry(self, mock_chat) -> None:
        review = quality_review("print('ok')", _fast_task_plan("print ok"))
        self.assertFalse(review.passed)
        self.assertIn("QA unavailable", review.issues[0])
        self.assertEqual(mock_chat.call_count, 2)

    @patch("inference.inferenceFast.repair_code")
    @patch("inference.inferenceFast.quality_review", return_value=ReviewResult(False, ["QA unavailable: empty response"]))
    @patch("inference.inferenceFast.validate_code", return_value=ValidationResult(True))
    @patch("inference.inferenceFast.write_code", return_value="print('ok')")
    @patch("inference.inferenceFast.analyze_task", return_value=_fast_task_plan("print ok"))
    @patch("inference.inferenceFast.ENABLE_ACCEPTANCE_TESTS", False)
    def test_unavailable_qa_stops_without_blind_repair(self, analyze, write, validate, review, repair) -> None:
        result = project_management_with_attempts("print ok", max_retries=1)
        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.attempts), 1)
        repair.assert_not_called()

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

    def test_runtime_check_rejects_non_exiting_smoke_test(self) -> None:
        result = runtime_check("while True: pass", startup_grace=0.2)
        self.assertFalse(result.passed)
        self.assertIn("Smoke test did not exit", result.failures[0])

    def test_acceptance_tests_can_inspect_candidate(self) -> None:
        result = run_acceptance_tests(
            "def add(left, right):\n    return left + right\n",
            "import importlib.util\nimport os\n"
            "spec = importlib.util.spec_from_file_location('candidate', os.environ['CANDIDATE_PATH'])\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "assert module.add(2, 3) == 5\n",
        )
        self.assertTrue(result.passed)
        self.assertTrue(result.executed)

    def test_acceptance_test_failure_is_reported(self) -> None:
        result = run_acceptance_tests("value = 1\n", "raise AssertionError('missing behavior')\n")
        self.assertFalse(result.passed)
        self.assertTrue(result.executed)
        self.assertIn("Acceptance failure", result.failures[0])


if __name__ == "__main__":
    unittest.main()
