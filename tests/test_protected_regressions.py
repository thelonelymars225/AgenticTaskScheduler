"""Regression checks for CLI families that the evaluator change must not break."""
from pathlib import Path
import unittest

from inference.inferenceFast import run_acceptance_tests


ROOT = Path(__file__).resolve().parent.parent


class ProtectedRegressionTests(unittest.TestCase):
    def assert_pair_passes(self, candidate_path: Path, tests_path: Path) -> None:
        result = run_acceptance_tests(
            candidate_path.read_text(encoding="utf-8"),
            tests_path.read_text(encoding="utf-8"),
            timeout=10,
        )
        self.assertEqual(result.measurement_status, "VALID", result.failures)
        self.assertTrue(result.passed, result.failures)
        self.assertGreater(result.test_count, 0)
        self.assertEqual(result.exit_code, 0)

    def test_todo_cli_stored_fixture(self) -> None:
        attempt = ROOT / "runs" / "20260718-021307" / "attempt-01"
        self.assert_pair_passes(attempt / "candidate.py", attempt / "acceptance_tests.py")

    def test_config_validator_stored_fixture(self) -> None:
        attempt = ROOT / "runs" / "20260718-023840" / "attempt-01"
        self.assert_pair_passes(attempt / "candidate.py", attempt / "acceptance_tests.py")

    def test_log_summary_checked_in_fixture(self) -> None:
        fixtures = ROOT / "tests" / "fixtures"
        self.assert_pair_passes(
            fixtures / "log_summary_good.py",
            fixtures / "log_summary_acceptance.py",
        )


if __name__ == "__main__":
    unittest.main()
