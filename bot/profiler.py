"""
Minimal performance profiler for chrani-bot-tng

Only active when PROFILING_ENABLED=true environment variable is set.
"""

import os
from time import time
from collections import defaultdict, deque
from datetime import datetime


class Profiler:
    def __init__(self):
        self._metrics = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "min_time": float('inf'),
            "max_time": 0,
            "samples": deque(maxlen=100)
        })
        self._enabled = os.getenv('PROFILING_ENABLED', '').lower() == 'true'
        self._log_file = None
        self._write_counter = 0
        self._write_interval = 100  # Write stats every 100 measurements

        if self._enabled:
            # Create log file with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagnostic_logs')
            os.makedirs(log_dir, exist_ok=True)
            self._log_file = os.path.join(log_dir, f'profiling_{timestamp}.log')

            # Write header
            with open(self._log_file, 'w') as f:
                f.write(f"Profiling started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")

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

            # Calculate p95 (95th percentile)
            samples = sorted(metric["samples"])
            p95_idx = int(len(samples) * 0.95)
            p95 = samples[p95_idx] if samples else 0

            return {
                "count": metric["count"],
                "avg": avg,
                "p95": p95,
                "max": metric["max_time"]
            }

    def write_stats(self):
        """Write current stats to log file."""
        if not self._enabled or not self._log_file:
            return

        with self._lock:
            timestamp = datetime.now().strftime('%H:%M:%S')
            with open(self._log_file, 'a') as f:
                for metric_name in self._metrics.keys():
                    stats = self.get_stats(metric_name)
                    if stats:
                        f.write(
                            f"[{timestamp}] {metric_name}: "
                            f"count={stats['count']} "
                            f"avg={stats['avg']*1000:.2f}ms "
                            f"p95={stats['p95']*1000:.2f}ms "
                            f"max={stats['max']*1000:.2f}ms\n"
                        )


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
