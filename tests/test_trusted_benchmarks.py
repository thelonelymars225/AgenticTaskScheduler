"""Self-tests for the checked-in benchmark oracles and evidence routing."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from inference.inferenceFast import (
    ReviewResult,
    ValidationResult,
    _acceptance_harness_violations,
    _fast_task_plan,
    project_management_with_attempts,
    run_acceptance_tests,
)
from inference.trusted_benchmarks import get_trusted_suite
from main import _write_attempt_artifacts


FIXTURES = Path(__file__).parent / "fixtures"


def fixture_source(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TrustedBenchmarkTests(unittest.TestCase):
    def assert_suite_passes(self, benchmark_id: str, source: str) -> None:
        suite = get_trusted_suite(benchmark_id)
        self.assertIsNotNone(suite)
        result = run_acceptance_tests(source, suite.source, timeout=10)
        self.assertEqual(result.measurement_status, "VALID", result.failures)
        self.assertTrue(result.executed)
        self.assertGreater(result.test_count, 0)
        self.assertEqual(result.exit_code, 0, result.failures)
        self.assertTrue(result.passed, result.failures)

    def assert_suite_rejects(self, benchmark_id: str, source: str, case: str) -> None:
        suite = get_trusted_suite(benchmark_id)
        self.assertIsNotNone(suite)
        result = run_acceptance_tests(source, suite.source, timeout=10)
        self.assertEqual(result.measurement_status, "VALID", f"{case}: {result.failures}")
        self.assertTrue(result.executed, case)
        self.assertGreater(result.test_count, 0, case)
        self.assertNotEqual(result.exit_code, 0, case)
        self.assertFalse(result.passed, case)

    def test_trusted_suites_are_runner_compatible(self) -> None:
        for benchmark_id in ("json_merge", "text_statistics"):
            with self.subTest(benchmark_id=benchmark_id):
                suite = get_trusted_suite(benchmark_id)
                self.assertIsNotNone(suite)
                self.assertEqual(_acceptance_harness_violations(suite.source), [])
                self.assertNotIn("pytest", suite.source)
                self.assertNotIn("tmp_path", suite.source)

    def test_json_merge_suite_passes_known_good(self) -> None:
        self.assert_suite_passes("json_merge", fixture_source("json_merge_good.py"))

    def test_json_merge_suite_rejects_broken_behaviors(self) -> None:
        good = fixture_source("json_merge_good.py")
        cases = {
            "list_element_merge": good.replace(
                "    return copy.deepcopy(right)\n",
                "    if isinstance(left, list) and isinstance(right, list):\n"
                "        return [merge(a, b) for a, b in zip(left, right)]\n"
                "    return copy.deepcopy(right)\n",
            ),
            "input_mutation": good.replace("result = copy.deepcopy(left)", "result = left"),
            "no_recursive_merge": good.replace(
                "result[key] = merge(result[key], value) if key in result else copy.deepcopy(value)",
                "result[key] = copy.deepcopy(value)",
            ),
            "ignores_malformed_json": good.replace(
                "        return json.load(handle)",
                "        try:\n            return json.load(handle)\n        except json.JSONDecodeError:\n            return {}",
            ),
            "incorrect_cli_paths": good.replace(
                "left = _load(Path(sys.argv[1]))\n        right = _load(Path(sys.argv[2]))",
                "left = _load(Path('left.json'))\n        right = _load(Path('right.json'))",
            ),
        }
        for case, source in cases.items():
            with self.subTest(case=case):
                self.assert_suite_rejects("json_merge", source, case)

    def test_text_statistics_suite_passes_known_good(self) -> None:
        self.assert_suite_passes("text_statistics", fixture_source("text_statistics_good.py"))

    def test_text_statistics_suite_rejects_broken_behaviors(self) -> None:
        good = fixture_source("text_statistics_good.py")
        cases = {
            "incorrect_empty": good.replace('"words": len(tokens)', '"words": len(tokens) if text else 1'),
            "case_sensitive": good.replace("token.lower()", "token"),
            "punctuation_tokens": good.replace(
                're.findall(r"\\w+", text, flags=re.UNICODE)',
                "text.split()",
            ),
            "wrong_character_count": good.replace('"characters": len(text)', '"characters": len(text.strip())'),
            "sys_exit_in_library": good.replace(
                "def analyze_file(path):\n    return analyze_text(Path(path).read_text(encoding=\"utf-8\"))",
                "def analyze_file(path):\n    if not Path(path).exists():\n        raise SystemExit(2)\n    return analyze_text(Path(path).read_text(encoding=\"utf-8\"))",
            ),
            "cwd_dependency": good.replace(
                "return analyze_text(Path(path).read_text(encoding=\"utf-8\"))",
                "return analyze_text(Path(Path(path).name).read_text(encoding=\"utf-8\"))",
            ),
            "missing_unicode": good.replace("flags=re.UNICODE", "flags=re.ASCII"),
        }
        for case, source in cases.items():
            with self.subTest(case=case):
                self.assert_suite_rejects("text_statistics", source, case)

    @patch("inference.inferenceFast.quality_review")
    @patch("inference.inferenceFast.write_acceptance_tests")
    @patch("inference.inferenceFast.validate_code", return_value=ValidationResult(True))
    @patch("inference.inferenceFast.write_code")
    @patch("inference.inferenceFast.analyze_task")
    def test_known_benchmark_bypasses_generated_oracle_and_llm_review(
        self, analyze, write, validate, generated_tests, review
    ) -> None:
        analyze.return_value = _fast_task_plan("json merge")
        write.return_value = fixture_source("json_merge_good.py")
        result = project_management_with_attempts("json merge", benchmark_id="json_merge")
        generated_tests.assert_not_called()
        review.assert_not_called()
        self.assertEqual(result.trusted_suite_version, "1.0.0")
        self.assertEqual(result.attempts[-1].candidate_status, "PASS")
        self.assertEqual(result.attempts[-1].acceptance_result.measurement_status, "VALID")

    @patch("inference.inferenceFast.validate_code", return_value=ValidationResult(True))
    @patch("inference.inferenceFast.repair_code")
    @patch("inference.inferenceFast.write_code")
    @patch("inference.inferenceFast.analyze_task")
    def test_repair_events_record_changed_and_unchanged_invocations(
        self, analyze, write, repair, validate
    ) -> None:
        analyze.return_value = _fast_task_plan("json merge")
        good = fixture_source("json_merge_good.py")
        bad = good.replace("return copy.deepcopy(right)", "return copy.deepcopy(left)")
        write.return_value = bad
        repair.return_value = good
        changed = project_management_with_attempts(
            "json merge", max_retries=1, benchmark_id="json_merge"
        )
        self.assertEqual(len(changed.repair_events), 1)
        self.assertEqual(changed.repair_events[0].status, "CHANGED")
        self.assertTrue(changed.repair_events[0].changed)
        self.assertNotEqual(changed.repair_events[0].before_sha256, changed.repair_events[0].after_sha256)
        self.assertEqual(changed.attempts[0].repair_status, "NOT_ATTEMPTED")
        self.assertEqual(changed.attempts[1].repair_status, "CHANGED")
        with tempfile.TemporaryDirectory(prefix="manifest-test-") as directory:
            run_dir = _write_attempt_artifacts(Path(directory), changed, "json_merge")
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["repair_count"], 1)
        self.assertEqual(manifest["repair_events"][0]["status"], "CHANGED")
        self.assertFalse(manifest["attempts"][0]["repair_changed_code"])
        self.assertTrue(manifest["attempts"][1]["repair_changed_code"])
        self.assertEqual(manifest["measurement_status"], "VALID")
        self.assertEqual(manifest["candidate_status"], "PASS")

        write.return_value = bad
        repair.return_value = bad
        unchanged = project_management_with_attempts(
            "json merge", max_retries=1, benchmark_id="json_merge"
        )
        self.assertEqual(len(unchanged.attempts), 1)
        self.assertEqual(len(unchanged.repair_events), 1)
        self.assertEqual(unchanged.repair_events[0].status, "UNCHANGED")
        self.assertFalse(unchanged.repair_events[0].changed)
        self.assertEqual(unchanged.repair_events[0].before_sha256, unchanged.repair_events[0].after_sha256)


if __name__ == "__main__":
    unittest.main()
