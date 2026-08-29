"""Lightweight performance measurement and latency instrumentation utilities (Phases 1 & 2)."""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger("performance")

_perf_metrics: Dict[str, list] = {}


@contextmanager
def measure(
    operation_name: str,
    extra_meta: Optional[Dict[str, Any]] = None,
    log_level: int = logging.INFO,
) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager that records execution duration of operations with sub-millisecond precision.

    Example:
        with measure("pinecone_query", {"top_k": 4}) as m:
            results = index.query(...)
        print(m["duration_ms"])
    """
    context: Dict[str, Any] = {
        "operation": operation_name,
        "start_time": time.perf_counter(),
        "duration_ms": 0.0,
        "metadata": extra_meta or {},
    }
    try:
        yield context
    finally:
        end_time = time.perf_counter()
        duration_ms = (end_time - context["start_time"]) * 1000.0
        context["duration_ms"] = round(duration_ms, 2)

        # Record in in-memory performance registry
        if operation_name not in _perf_metrics:
            _perf_metrics[operation_name] = []
        _perf_metrics[operation_name].append(duration_ms)

        meta_str = f" | meta: {extra_meta}" if extra_meta else ""
        logger.log(
            log_level,
            f"[PERF] {operation_name}: {duration_ms:.2f} ms{meta_str}",
        )


def get_performance_summary() -> Dict[str, Dict[str, float]]:
    """Returns aggregated average, min, max, and count metrics for all instrumented operations."""
    summary = {}
    for op, timings in _perf_metrics.items():
        if not timings:
            continue
        summary[op] = {
            "count": len(timings),
            "avg_ms": round(sum(timings) / len(timings), 2),
            "min_ms": round(min(timings), 2),
            "max_ms": round(max(timings), 2),
            "latest_ms": round(timings[-1], 2),
        }
    return summary


def reset_performance_metrics() -> None:
    """Clears all recorded performance metrics."""
    _perf_metrics.clear()
