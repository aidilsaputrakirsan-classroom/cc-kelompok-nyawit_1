"""
Error Alert Checker.
Background thread yang memeriksa error rate setiap interval tertentu.
Jika error rate > threshold dalam 1 menit terakhir, emit log CRITICAL
dengan field `alert: true` agar bisa di-pick up log aggregator.
"""
import logging
import os
import threading
import time

from metrics import metrics

logger = logging.getLogger(__name__)

# Konfigurasi via environment variable
CHECK_INTERVAL_SECONDS = int(os.getenv("ALERT_CHECK_INTERVAL", "10"))
ERROR_RATE_THRESHOLD = float(os.getenv("ALERT_ERROR_RATE_THRESHOLD", "10"))
WINDOW_SECONDS = int(os.getenv("ALERT_WINDOW_SECONDS", "60"))
# Cooldown: jangan spam alert, tunggu minimal N detik setelah alert terakhir
ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN", "60"))


class ErrorAlertChecker:
    """Daemon thread yang cek error rate dan emit CRITICAL alert."""

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_alert_time: float = 0

    def start(self):
        """Start background checker. Idempotent — tidak membuat thread duplikat."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="error-alert-checker", daemon=True
        )
        self._thread.start()
        logger.info(
            f"ErrorAlertChecker started (interval={CHECK_INTERVAL_SECONDS}s, "
            f"threshold={ERROR_RATE_THRESHOLD}%, window={WINDOW_SECONDS}s)"
        )

    def stop(self):
        """Stop background checker."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def _run(self):
        """Loop: cek error rate setiap CHECK_INTERVAL_SECONDS."""
        while not self._stop_event.is_set():
            try:
                self._check()
            except Exception as e:
                logger.warning(f"ErrorAlertChecker error: {e}")

            # Cleanup old entries di sliding window
            metrics.cleanup_recent()

            self._stop_event.wait(CHECK_INTERVAL_SECONDS)

    def _check(self):
        """Cek error rate 1 menit terakhir, emit CRITICAL jika di atas threshold."""
        result = metrics.get_recent_error_rate(window_seconds=WINDOW_SECONDS)

        total = result["total_requests"]
        errors = result["total_errors"]
        rate = result["error_rate_percent"]

        # Jangan alert jika belum ada request yang cukup dalam window
        if total < 1:
            return

        if rate > ERROR_RATE_THRESHOLD:
            now = time.time()
            # Cooldown: hindari spam alert
            if (now - self._last_alert_time) < ALERT_COOLDOWN_SECONDS:
                return

            self._last_alert_time = now
            logger.critical(
                (
                    f"HIGH ERROR RATE ALERT: {rate}% errors in last "
                    f"{WINDOW_SECONDS}s ({errors}/{total} requests)"
                ),
                extra={
                    "alert": True,
                    "alert_type": "high_error_rate",
                    "error_rate_percent": rate,
                    "error_count": errors,
                    "request_count": total,
                    "window_seconds": WINDOW_SECONDS,
                    "threshold_percent": ERROR_RATE_THRESHOLD,
                },
            )
        else:
            # Log DEBUG saat normal (tidak mengganggu production log)
            logger.debug(
                f"Error rate OK: {rate}% ({errors}/{total} in {WINDOW_SECONDS}s)"
            )


# Singleton instance
alert_checker = ErrorAlertChecker()
