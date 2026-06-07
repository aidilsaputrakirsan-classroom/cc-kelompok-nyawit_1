"""
Request Logging Middleware.
Log setiap HTTP request dengan timing, status, correlation ID, dan metrics.
Juga memulai ErrorAlertChecker background thread.
"""
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from metrics import metrics
from alert_checker import alert_checker

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware yang log setiap request/response dan record metrics."""

    def __init__(self, app):
        super().__init__(app)
        # Start error alert checker (idempotent, aman dipanggil berulang)
        alert_checker.start()

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get(
            "X-Correlation-ID", str(uuid.uuid4())[:12]
        )
        request.state.correlation_id = correlation_id
        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            metrics.record_request(request.method, request.url.path, 500, duration_ms)
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "status_code": 500,
                },
            )
            raise

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Record metrics untuk semua request
        metrics.record_request(
            request.method, request.url.path,
            response.status_code, duration_ms
        )

        # Skip log health/metrics agar tidak noisy
        if request.url.path not in ["/health", "/metrics"]:
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

        response.headers["X-Correlation-ID"] = correlation_id
        return response
