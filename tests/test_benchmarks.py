"""Tests for the deterministic benchmark selector."""
import unittest

from inference.benchmarks import FOCUSED_CLI_BENCHMARKS, select_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_selector_balances_focused_benchmarks(self) -> None:
        self.assertEqual(
            {task.identifier for task in FOCUSED_CLI_BENCHMARKS},
            {"json_merge", "text_statistics"},
        )
        self.assertNotEqual(select_benchmark(0).identifier, select_benchmark(1).identifier)
        self.assertEqual(select_benchmark(0), select_benchmark(len(FOCUSED_CLI_BENCHMARKS)))
