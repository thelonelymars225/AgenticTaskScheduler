"""Tests for the deterministic benchmark selector."""
import unittest

from inference.benchmarks import BENCHMARKS, select_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_selector_rotates_and_repeats(self) -> None:
        self.assertGreaterEqual(len(BENCHMARKS), 4)
        self.assertNotEqual(select_benchmark(0).identifier, select_benchmark(1).identifier)
        self.assertEqual(select_benchmark(0), select_benchmark(len(BENCHMARKS)))
