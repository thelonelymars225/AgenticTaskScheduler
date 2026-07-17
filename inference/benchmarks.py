"""Small, stable benchmark set for measuring pipeline improvements.

Each task is intentionally standard-library only so the acceptance-test runner
can verify behavior without external services or installed packages.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkTask:
    identifier: str
    prompt: str


BENCHMARKS: tuple[BenchmarkTask, ...] = (
    BenchmarkTask(
        "pong_tkinter",
        "Write a Python Pong game using tkinter and object-oriented programming. "
        "It must support two paddles, ball movement, wall and paddle collisions, scoring, restart after a score, "
        "keyboard controls, and AGENT_SMOKE_TEST=1 must exit without opening a window.",
    ),
    BenchmarkTask(
        "todo_cli",
        "Write a standard-library Python command-line todo application. It must persist tasks as JSON, support add, "
        "list, complete, and remove commands, validate malformed stored data, return useful exit codes, and expose "
        "the storage operations as importable functions for tests.",
    ),
    BenchmarkTask(
        "config_validator",
        "Write a standard-library Python configuration validator. It must load JSON from a file, validate required "
        "string, integer-range, and boolean fields, report all validation errors, provide an importable validate_config "
        "function, and include a command-line interface with useful exit codes.",
    ),
    BenchmarkTask(
        "text_statistics",
        "Write a standard-library Python text statistics tool. It must expose importable functions that count lines, "
        "words, characters, and case-insensitive word frequencies, handle empty Unicode text, and provide a command-line "
        "interface that reads a UTF-8 file and emits JSON.",
    ),
)


def select_benchmark(completed_runs: int) -> BenchmarkTask:
    """Choose benchmarks deterministically, so results are comparable by commit."""
    return BENCHMARKS[completed_runs % len(BENCHMARKS)]
