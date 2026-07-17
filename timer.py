"""
Performance timer utility for monitoring execution time of code blocks.

Usage:
    # As a context manager
    with Timer("business_analysis"):
        result = business_analysis(prompt)

    # As a decorator
    @Timer.timed
    def my_function():
        ...

    # Manual start/stop
    t = Timer("code_generation")
    t.start()
    ...
    t.stop()

    # Print all recorded timings
    Timer.print_stats()
"""

import time
import logging
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)


class Timer:
    """A simple yet powerful timer for performance monitoring."""

    _timings: dict[str, list[float]] = defaultdict(list)
    _active: dict[str, float] = {}

    def __init__(self, name: str, log_level: int = logging.DEBUG):
        self.name = name
        self.log_level = log_level
        self._start_time: float | None = None
        self._elapsed: float | None = None

    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.perf_counter()
        Timer._active[self.name] = self._start_time

    def stop(self) -> float:
        """Stop the timer and record the elapsed time.

        Returns:
            Elapsed time in seconds.
        """
        if self._start_time is None:
            raise RuntimeError(f"Timer '{self.name}' was never started.")

        elapsed = time.perf_counter() - self._start_time
        self._elapsed = elapsed
        Timer._timings[self.name].append(elapsed)
        Timer._active.pop(self.name, None)

        logger.log(self.log_level, "%s took %.4fs", self.name, elapsed)
        return elapsed

    def reset(self) -> None:
        """Reset this timer instance."""
        self._start_time = None
        self._elapsed = None

    @property
    def elapsed(self) -> float | None:
        return self._elapsed

    # ── Context manager ──────────────────────────────────────────────

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    # ── Decorator ────────────────────────────────────────────────────

    @staticmethod
    def timed(func):
        """Decorator that times the decorated function."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            name = f"{func.__module__}.{func.__qualname__}"
            with Timer(name):
                return func(*args, **kwargs)

        return wrapper

    # ── Statistics ───────────────────────────────────────────────────

    @classmethod
    def reset_all(cls) -> None:
        """Clear all recorded timings."""
        cls._timings.clear()
        cls._active.clear()

    @classmethod
    def get_stats(cls) -> dict[str, dict[str, float]]:
        """Get aggregate statistics for each named timer.

        Returns:
            Dict mapping timer names to dicts with keys:
            count, total, mean, min, max, last.
        """
        stats = {}
        for name, times in cls._timings.items():
            if not times:
                continue
            stats[name] = {
                "count": len(times),
                "total": sum(times),
                "mean": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "last": times[-1],
            }
        return stats

    @classmethod
    def print_stats(cls, title: str = "⏱ Performance Timings") -> None:
        """Print a formatted table of all recorded timings to stdout."""
        stats = cls.get_stats()
        if not stats:
            print("No timings recorded.")
            return

        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
        print(f"{'Name':<30} {'Count':>6} {'Total (s)':>10} {'Mean (s)':>10} {'Min (s)':>10} {'Max (s)':>10}")
        print(f"{'-' * 76}")
        for name, s in sorted(stats.items(), key=lambda x: x[1]["total"], reverse=True):
            print(
                f"{name:<30} {s['count']:>6} {s['total']:>10.4f} {s['mean']:>10.4f} "
                f"{s['min']:>10.4f} {s['max']:>10.4f}"
            )
        print(f"{'=' * 60}")
