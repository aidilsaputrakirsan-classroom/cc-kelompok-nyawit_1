"""
Circuit Breaker — mencegah cascading failure saat Auth Service gagal berulang.

State: CLOSED (normal) → OPEN (fail fast) → HALF_OPEN (test recovery) → CLOSED
"""

import logging
import time

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Simple circuit breaker.

    - CLOSED:    Request diteruskan ke target service.
    - OPEN:      Request langsung ditolak (fail fast).
    - HALF_OPEN: 1 request diizinkan untuk test recovery.
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        cooldown_seconds: int = 30,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        self.failure_count = 0
        self.success_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None
        self.total_rejected = 0

    def can_execute(self) -> bool:
        """Return True jika request boleh diteruskan, False jika ditolak (OPEN)."""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.cooldown_seconds:
                logger.info(
                    f"[CircuitBreaker:{self.name}] "
                    f"Cooldown selesai. OPEN → HALF_OPEN"
                )
                self.state = "HALF_OPEN"
                return True
            else:
                self.total_rejected += 1
                return False

        # HALF_OPEN — izinkan 1 request test
        return True

    def record_success(self):
        """Catat keberhasilan. Reset failure count, kembali ke CLOSED."""
        if self.state == "HALF_OPEN":
            logger.info(
                f"[CircuitBreaker:{self.name}] Test berhasil. HALF_OPEN → CLOSED"
            )
        self.failure_count = 0
        self.success_count += 1
        self.state = "CLOSED"

    def record_failure(self):
        """Catat kegagalan. Jika threshold tercapai → OPEN."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "HALF_OPEN":
            logger.warning(
                f"[CircuitBreaker:{self.name}] Test gagal. HALF_OPEN → OPEN"
            )
            self.state = "OPEN"
        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"[CircuitBreaker:{self.name}] "
                f"Threshold tercapai ({self.failure_count}/{self.failure_threshold}). "
                f"CLOSED → OPEN"
            )
            self.state = "OPEN"

    def get_status(self) -> dict:
        """Return status circuit breaker untuk health check."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "total_rejected": self.total_rejected,
            "cooldown_seconds": self.cooldown_seconds,
        }
