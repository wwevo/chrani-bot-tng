"""
Performance Profiler for chrani-bot-tng

Instruments critical paths to measure timing and identify bottlenecks.
"""

from time import time
from collections import defaultdict, deque
from threading import Lock
from bot.logger import get_logger

logger = get_logger("profiler")


class Profiler:
    """
    Lightweight profiler to track timing of critical operations.

    Usage:
        with profiler.measure("operation_name"):
            # code to profile
            pass
    """

    def __init__(self, max_samples_per_metric=100):
        self._metrics = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "min_time": float('inf'),
            "max_time": 0,
            "samples": deque(maxlen=max_samples_per_metric)
        })
        self._lock = Lock()
        self._enabled = True

    def enable(self):
        """Enable profiling."""
        self._enabled = True

    def disable(self):
        """Disable profiling (no overhead)."""
        self._enabled = False

    def measure(self, metric_name):
        """Context manager for measuring execution time."""
        return _ProfilerContext(self, metric_name)

    def record(self, metric_name, duration):
        """Record a timing measurement."""
        if not self._enabled:
            return

        with self._lock:
            metric = self._metrics[metric_name]
            metric["count"] += 1
            metric["total_time"] += duration
            metric["min_time"] = min(metric["min_time"], duration)
            metric["max_time"] = max(metric["max_time"], duration)
            metric["samples"].append(duration)

    def get_stats(self, metric_name):
        """Get statistics for a metric."""
        with self._lock:
            metric = self._metrics[metric_name]
            if metric["count"] == 0:
                return None

            avg = metric["total_time"] / metric["count"]

            # Calculate median from samples
            samples = sorted(metric["samples"])
            if samples:
                mid = len(samples) // 2
                median = samples[mid] if len(samples) % 2 else (samples[mid-1] + samples[mid]) / 2
            else:
                median = 0

            # Calculate p95 (95th percentile)
            p95_idx = int(len(samples) * 0.95)
            p95 = samples[p95_idx] if samples else 0

            return {
                "count": metric["count"],
                "total": metric["total_time"],
                "avg": avg,
                "min": metric["min_time"],
                "max": metric["max_time"],
                "median": median,
                "p95": p95
            }

    def get_all_stats(self):
        """Get statistics for all metrics."""
        with self._lock:
            stats = {}
            for name in self._metrics.keys():
                stats[name] = self.get_stats(name)
            return stats

    def log_stats(self, metric_names=None):
        """Log statistics to logger."""
        if metric_names is None:
            metric_names = list(self._metrics.keys())

        for name in metric_names:
            stats = self.get_stats(name)
            if stats:
                logger.info(
                    "profiler_stats",
                    metric=name,
                    count=stats["count"],
                    avg_ms=round(stats["avg"] * 1000, 2),
                    median_ms=round(stats["median"] * 1000, 2),
                    p95_ms=round(stats["p95"] * 1000, 2),
                    min_ms=round(stats["min"] * 1000, 2),
                    max_ms=round(stats["max"] * 1000, 2)
                )

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()


class _ProfilerContext:
    """Context manager for profiling."""

    def __init__(self, profiler, metric_name):
        self.profiler = profiler
        self.metric_name = metric_name
        self.start_time = None

    def __enter__(self):
        if self.profiler._enabled:
            self.start_time = time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profiler._enabled and self.start_time is not None:
            duration = time() - self.start_time
            self.profiler.record(self.metric_name, duration)


# Global profiler instance
profiler = Profiler()
