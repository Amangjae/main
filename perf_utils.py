"""Simple performance helpers for local profiling."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)


class PerformanceTracker:
    def __init__(self) -> None:
        self.timings: dict[str, list[float]] = defaultdict(list)

    def record(self, name: str, duration_ms: float) -> None:
        self.timings[name].append(duration_ms)
        logger.info("%s took %.2fms", name, duration_ms)

    def summary(self) -> dict[str, dict[str, float]]:
        return {
            name: {
                "count": float(len(values)),
                "avg_ms": sum(values) / len(values),
                "max_ms": max(values),
            }
            for name, values in self.timings.items()
        }


_tracker = PerformanceTracker()


def measure_performance(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            _tracker.record(name, (time.perf_counter() - start) * 1000)
            return result

        return wrapper

    return decorator


def get_tracker() -> PerformanceTracker:
    return _tracker
