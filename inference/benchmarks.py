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
        "Write a standard-library Python text statistics tool with one fixed contract. Expose importable core functions. "
        "None and unsupported non-string values raise TypeError. Empty and whitespace-only strings have zero words and "
        "an empty frequency mapping. Character count uses the original text; line count is zero for empty text and "
        "otherwise counts logical lines. Tokenize Unicode words deterministically, remove surrounding punctuation, "
        "normalize words to lowercase, and return frequency mappings in deterministic lexical key order. File functions "
        "accept an explicit path, read UTF-8, propagate FileNotFoundError and UnicodeDecodeError, and never call sys.exit. "
        "The CLI accepts an explicit input path, emits stable JSON, reports errors on stderr, and uses useful exit codes.",
    ),
    BenchmarkTask(
        "json_merge",
        "Write a standard-library Python JSON merge utility with one fixed contract. Expose an importable merge(left, right) "
        "function. When both values are objects, recursively merge their keys; preserve non-conflicting keys, and let the right "
        "value replace the left value for scalar, list, type-mismatch, and every other non-object conflict. Do not mutate either "
        "input. The CLI requires explicit left-input, right-input, and output paths, reads and writes UTF-8 JSON, writes stable "
        "JSON with sorted keys, reports malformed JSON and file errors on stderr, and returns useful non-zero exit codes.",
    ),
    BenchmarkTask(
        "log_summary",
        "Write a standard-library Python log summarizer. It must parse timestamped level/message lines, count levels including empty input, "
        "expose an importable summarize function, and provide a CLI that reads UTF-8 input and emits stable JSON.",
    ),
)

# Keep the focused measurement phase deterministic and free of display dependencies.
# Pong and the protected CLI families remain available for later regression runs.
BENCHMARK_MODE = "focused_cli"
CLI_BENCHMARKS = tuple(task for task in BENCHMARKS if task.identifier != "pong_tkinter")
FOCUSED_CLI_BENCHMARKS = tuple(
    task for task in BENCHMARKS if task.identifier in {"json_merge", "text_statistics"}
)


def select_benchmark(completed_runs: int) -> BenchmarkTask:
    """Choose benchmarks deterministically, so results are comparable by commit."""
    if BENCHMARK_MODE == "focused_cli":
        active = FOCUSED_CLI_BENCHMARKS
    elif BENCHMARK_MODE == "cli":
        active = CLI_BENCHMARKS
    else:
        active = BENCHMARKS
    return active[completed_runs % len(active)]
