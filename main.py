"""Cron-friendly command-line entry point."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from inference.benchmarks import select_benchmark
from inference.inferenceFast import PipelineResult, _strip_code_blocks, project_management_with_attempts
from inference.pipeline_config import CODER_MODEL
from timer import Timer


def _attempt_classification(result: PipelineResult) -> str:
    """Classify the final attempt from executable evidence, failing closed."""
    attempt = result.attempts[-1]
    acceptance = attempt.acceptance_result
    if (
        attempt.validation.passed
        and acceptance.executed
        and acceptance.test_count > 0
        and acceptance.exit_code == 0
        and acceptance.passed
        and attempt.review.passed
    ):
        return "PASS"
    if any("unchanged candidate" in issue.lower() for issue in result.review.issues):
        return "UNCHANGED_REPAIR"
    if any(failure.startswith("Invalid acceptance harness:") for failure in acceptance.failures):
        return "HARNESS_FAIL"
    if not acceptance.executed:
        return "NO_TESTS_COLLECTED" if acceptance.test_count == 0 else "NOT_EXECUTED"
    return "CANDIDATE_FAIL"


def _write_attempt_artifacts(output_dir: Path, result: PipelineResult, benchmark_id: str | None = None) -> Path:
    """Persist every generated candidate and its evidence for later analysis."""
    started_at = datetime.now().astimezone()
    run_dir = output_dir / "runs" / started_at.strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "task": result.task.as_markdown(),
        "benchmark_id": benchmark_id,
        "run_timestamp": started_at.isoformat(),
        "attempt_count": len(result.attempts),
        "model_used": CODER_MODEL,
        "selected_candidate": result.attempts[-1].number,
        "repair_count": max(0, len(result.attempts) - 1),
        "final_classification": _attempt_classification(result),
        "final_verdict": result.review.as_text(),
        "attempts": [],
    }
    for index, attempt in enumerate(result.attempts):
        attempt_dir = run_dir / f"attempt-{attempt.number:02d}"
        attempt_dir.mkdir()
        (attempt_dir / "candidate.py").write_text(_strip_code_blocks(attempt.code), encoding="utf-8")
        (attempt_dir / "acceptance_tests.py").write_text(attempt.acceptance_tests, encoding="utf-8")
        validation = {
            "passed": attempt.validation.passed,
            "failures": attempt.validation.failures,
            "stdout": attempt.validation.stdout,
            "stderr": attempt.validation.stderr,
        }
        acceptance = {
            "passed": attempt.acceptance_result.passed,
            "failures": attempt.acceptance_result.failures,
            "stdout": attempt.acceptance_result.stdout,
            "stderr": attempt.acceptance_result.stderr,
            "executed": attempt.acceptance_result.executed,
            "test_count": attempt.acceptance_result.test_count,
            "exit_code": attempt.acceptance_result.exit_code,
        }
        review = {
            "passed": attempt.review.passed,
            "issues": attempt.review.issues,
            "raw": attempt.review.raw,
        }
        (attempt_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
        (attempt_dir / "acceptance_result.json").write_text(json.dumps(acceptance, indent=2), encoding="utf-8")
        (attempt_dir / "review.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
        manifest["attempts"].append({
            "number": attempt.number,
            "path": attempt_dir.name,
            "validation_passed": attempt.validation.passed,
            "acceptance_passed": attempt.acceptance_result.passed,
            "acceptance_executed": attempt.acceptance_result.executed,
            "collected_test_count": attempt.acceptance_result.test_count,
            "acceptance_exit_code": attempt.acceptance_result.exit_code,
            "review_passed": attempt.review.passed,
            "repair_changed_code": index == 0 or attempt.code.strip() != result.attempts[index - 1].code.strip(),
        })
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return run_dir


def main() -> int:
    """Run one generation task and return a cron-friendly exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="*")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt = " ".join(args.prompt).strip()
    benchmark_id: str | None = None
    if not prompt:
        completed_runs = sum(1 for path in (output_dir / "runs").glob("*/manifest.json")) if (output_dir / "runs").exists() else 0
        benchmark = select_benchmark(completed_runs)
        prompt = benchmark.prompt
        benchmark_id = benchmark.identifier

    with Timer("pipeline.total"):
        result = project_management_with_attempts(prompt)

    analysis = result.task.as_markdown()
    code = result.code
    qa_result = result.review.as_text()
    run_dir = _write_attempt_artifacts(output_dir, result, benchmark_id)

    (output_dir / "output.txt").write_text(
        f"=== Analysis ===\n{analysis}\n\n=== Code ===\n{code}\n\n=== QA Result ===\n{qa_result}\n",
        encoding="utf-8",
    )

    clean_code = _strip_code_blocks(code)
    if not clean_code:
        print("No executable code was generated")
        return 1

    output_path = output_dir / "output.py"
    output_path.write_text(clean_code, encoding="utf-8")
    print(f"Written {len(clean_code)} characters to {output_path}")
    print(f"Saved {len(result.attempts)} attempt record(s) to {run_dir}")
    print(qa_result)
    return 0 if qa_result.startswith("VERDICT: PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
