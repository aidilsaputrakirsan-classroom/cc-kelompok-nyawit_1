"""
Simple In-Memory Metrics Collector.
Mengumpulkan metrics dasar: request count, error count, latency.
"""
import time
import threading
from collections import defaultdict


class MetricsCollector:
    """Thread-safe metrics collector."""

    def __init__(self):
        self._lock = threading.Lock()
        self.start_time = time.time()

        self.request_count = 0
        self.error_count = 0
        self.status_counts = defaultdict(int)

        self.latencies = []
        self.max_latency_samples = 1000

        # Sliding window: list of (timestamp, is_error) untuk hitung error rate terkini
        self.recent_requests: list[tuple[float, bool]] = []
        self.recent_window_seconds = 120  # simpan data 2 menit (cleanup > window cek)

        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "errors": 0,
            "total_latency_ms": 0,
        })

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Catat satu request."""
        with self._lock:
            self.request_count += 1
            self.status_counts[status_code] += 1

            is_error = status_code >= 400
            if is_error:
                self.error_count += 1

            # Catat ke sliding window untuk error rate terkini
            now = time.time()
            self.recent_requests.append((now, is_error))

            self.latencies.append(duration_ms)
            if len(self.latencies) > self.max_latency_samples:
                self.latencies.pop(0)

            key = f"{method} {path}"
            self.endpoint_stats[key]["count"] += 1
            self.endpoint_stats[key]["total_latency_ms"] += duration_ms
            if is_error:
                self.endpoint_stats[key]["errors"] += 1

    def get_metrics(self) -> dict:
        """Return snapshot metrics."""
        with self._lock:
            uptime = round(time.time() - self.start_time, 1)
            error_rate = (
                round(self.error_count / self.request_count * 100, 2)
                if self.request_count > 0 else 0
            )

            latency_stats = {}
            if self.latencies:
                sorted_lat = sorted(self.latencies)
                n = len(sorted_lat)
                latency_stats = {
                    "p50_ms": round(sorted_lat[int(n * 0.5)], 2),
                    "p95_ms": round(sorted_lat[int(n * 0.95)], 2),
                    "p99_ms": round(sorted_lat[min(int(n * 0.99), n - 1)], 2),
                    "avg_ms": round(sum(sorted_lat) / n, 2),
                }

            endpoints = {}
            for key, stats in self.endpoint_stats.items():
                avg_lat = (
                    round(stats["total_latency_ms"] / stats["count"], 2)
                    if stats["count"] > 0 else 0
                )
                endpoints[key] = {
                    "count": stats["count"],
                    "errors": stats["errors"],
                    "avg_latency_ms": avg_lat,
                }

            return {
                "uptime_seconds": uptime,
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "error_rate_percent": error_rate,
                "status_codes": dict(self.status_counts),
                "latency": latency_stats,
                "endpoints": endpoints,
            }

    def get_recent_error_rate(self, window_seconds: int = 60) -> dict:
        """
        Hitung error rate dalam window detik terakhir (sliding window).
        Return dict dengan: total, errors, error_rate_percent.
        """
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            recent = [(ts, err) for ts, err in self.recent_requests if ts >= cutoff]
            total = len(recent)
            errors = sum(1 for _, err in recent if err)
            rate = round(errors / total * 100, 2) if total > 0 else 0.0
        return {
            "window_seconds": window_seconds,
            "total_requests": total,
            "total_errors": errors,
            "error_rate_percent": rate,
        }

    def cleanup_recent(self):
        """Hapus entry sliding window yang sudah di luar 2x window cek."""
        now = time.time()
        cutoff = now - self.recent_window_seconds
        with self._lock:
            self.recent_requests = [
                (ts, err) for ts, err in self.recent_requests if ts >= cutoff
            ]

    def reset(self):
        """Reset semua metrics."""
        with self._lock:
            self.request_count = 0
            self.error_count = 0
            self.status_counts.clear()
            self.latencies.clear()
            self.endpoint_stats.clear()
            self.recent_requests.clear()


# Singleton instance
metrics = MetricsCollector()
