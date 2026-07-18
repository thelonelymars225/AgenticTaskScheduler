"""Tests for the deterministic benchmark selector."""
import unittest

from inference.benchmarks import CLI_BENCHMARKS, select_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_selector_rotates_and_repeats(self) -> None:
        self.assertGreaterEqual(len(CLI_BENCHMARKS), 5)
        self.assertNotEqual(select_benchmark(0).identifier, select_benchmark(1).identifier)
        self.assertEqual(select_benchmark(0), select_benchmark(len(CLI_BENCHMARKS)))
