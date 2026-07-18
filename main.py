"""Cron-friendly command-line entry point."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from inference.benchmarks import select_benchmark
from inference.inferenceFast import PipelineResult, _strip_code_blocks, project_management_with_attempts
from inference.pipeline_config import CODER_MODEL
from timer import Timer


def _attempt_classification(result: PipelineResult) -> str:
    """Compatibility classification derived from separate evidence fields."""
    attempt = result.attempts[-1]
    acceptance = attempt.acceptance_result
    if attempt.candidate_status == "PASS":
        return "PASS"
    if acceptance.measurement_status != "VALID":
        return acceptance.measurement_status
    return "CANDIDATE_FAIL"


def _sum_timings(timings: dict[str, float], prefix: str) -> float:
    return sum(duration for name, duration in timings.items() if name.startswith(prefix))


def _write_attempt_artifacts(output_dir: Path, result: PipelineResult, benchmark_id: str | None = None) -> Path:
    """Persist every generated candidate and its evidence for later analysis."""
    started_at = datetime.now().astimezone()
    run_dir = output_dir / "runs" / started_at.strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "task": result.task.as_markdown(),
        "benchmark_id": result.benchmark_id or benchmark_id,
        "run_timestamp": started_at.isoformat(),
        "attempt_count": len(result.attempts),
        "model_used": CODER_MODEL,
        "selected_candidate": result.attempts[-1].number,
        "measurement_status": result.attempts[-1].acceptance_result.measurement_status,
        "candidate_status": result.attempts[-1].candidate_status,
        "repair_status": result.repair_events[-1].status if result.repair_events else "NOT_ATTEMPTED",
        "repair_count": len(result.repair_events),
        "repair_events": [
            {
                "repair_number": event.repair_number,
                "source_attempt": event.source_attempt,
                "trigger": event.trigger,
                "before_sha256": event.before_sha256,
                "after_sha256": event.after_sha256,
                "changed": event.changed,
                "model": event.model,
                "status": event.status,
                "duration_seconds": event.duration_seconds,
            }
            for event in result.repair_events
        ],
        "trusted_suite_version": result.trusted_suite_version,
        "valid_evaluation": result.attempts[-1].acceptance_result.measurement_status == "VALID",
        "timings": result.timings,
        "generation_duration_seconds": _sum_timings(result.timings, "pipeline.generate"),
        "acceptance_generation_duration_seconds": _sum_timings(result.timings, "pipeline.acceptance.generate"),
        "acceptance_execution_duration_seconds": _sum_timings(result.timings, "pipeline.acceptance.run"),
        "review_duration_seconds": _sum_timings(result.timings, "pipeline.review"),
        "repair_duration_seconds": _sum_timings(result.timings, "pipeline.repair"),
        "total_duration_seconds": result.timings.get("pipeline.workflow"),
        "model_call_count": len(result.model_calls),
        "prompt_tokens": sum(call.get("prompt_tokens") or 0 for call in result.model_calls),
        "output_tokens": sum(call.get("output_tokens") or 0 for call in result.model_calls),
        "model_calls": result.model_calls,
        "final_classification": _attempt_classification(result),
        "final_verdict": result.review.as_text(),
        "attempts": [],
    }
    for attempt in result.attempts:
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
            "measurement_status": attempt.acceptance_result.measurement_status,
            "suite_version": attempt.acceptance_result.suite_version,
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
            "measurement_status": attempt.acceptance_result.measurement_status,
            "candidate_status": attempt.candidate_status,
            "review_passed": attempt.review.passed,
            "repair_status": attempt.repair_status,
            "repair_changed_code": attempt.repair_status == "CHANGED",
            "candidate_sha256": hashlib.sha256(attempt.code.encode("utf-8")).hexdigest(),
        })
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return run_dir


def main() -> int:
    """Run one generation task and return a cron-friendly exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="*")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--benchmark-id")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt = " ".join(args.prompt).strip()
    benchmark_id: str | None = args.benchmark_id
    if not prompt:
        completed_runs = sum(1 for path in (output_dir / "runs").glob("*/manifest.json")) if (output_dir / "runs").exists() else 0
        benchmark = select_benchmark(completed_runs)
        prompt = benchmark.prompt
        benchmark_id = benchmark.identifier

    with Timer("pipeline.total"):
        result = project_management_with_attempts(prompt, benchmark_id=benchmark_id)

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
    print(
        "Measurement: "
        f"{result.attempts[-1].acceptance_result.measurement_status}; "
        f"candidate: {result.attempts[-1].candidate_status}; "
        f"repairs: {len(result.repair_events)}"
    )
    print(qa_result)
    return 0 if qa_result.startswith("VERDICT: PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
