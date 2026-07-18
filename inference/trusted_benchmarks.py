"""Versioned, checked-in acceptance suites for stable benchmark IDs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrustedBenchmarkSuite:
    benchmark_id: str
    version: str
    contract: dict[str, object]
    source: str


_ROOT = Path(__file__).resolve().parent.parent / "benchmarks"


def get_trusted_suite(benchmark_id: str | None) -> TrustedBenchmarkSuite | None:
    """Load a trusted suite only for an explicitly supplied known benchmark ID."""
    if benchmark_id not in {"json_merge", "text_statistics"}:
        return None
    benchmark_dir = _ROOT / benchmark_id
    contract = json.loads((benchmark_dir / "contract.json").read_text(encoding="utf-8"))
    return TrustedBenchmarkSuite(
        benchmark_id=benchmark_id,
        version=str(contract["version"]),
        contract=contract,
        source=(benchmark_dir / "acceptance_tests.py").read_text(encoding="utf-8"),
    )
