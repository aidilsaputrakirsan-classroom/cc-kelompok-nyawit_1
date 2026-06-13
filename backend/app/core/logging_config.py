"""
Structured (JSON) logging + correlation ID untuk observability (Minggu 14).

Tiga hal yang disediakan modul ini:
1. `correlation_id_ctx` — ContextVar yang menyimpan correlation ID per-request.
2. `JsonFormatter` — formatter logging yang menghasilkan satu baris JSON per log,
   mudah di-parse/filter/aggregate oleh tools (Loki, CloudWatch, dsb.).
3. `setup_logging()` — konfigurasi root logger + uvicorn agar semua log seragam.

Correlation ID menghubungkan seluruh log yang menangani satu request yang sama,
sehingga satu alur request bisa ditelusuri lintas baris log.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# Disimpan per-request lewat middleware. Default "-" bila di luar konteks request
# (mis. log saat startup aplikasi).
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")

# Atribut bawaan LogRecord yang tidak perlu diulang di field "extra".
_RESERVED_LOG_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Format setiap LogRecord menjadi satu baris JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
        }

        # Sertakan info exception bila ada.
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Sertakan field tambahan yang dikirim via logger.info(..., extra={...}).
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_ATTRS and key not in log_entry:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    """
    Konfigurasi root logger agar memakai JSON formatter ke stdout.

    Level default INFO sesuai rekomendasi untuk production (Minggu 14).
    Uvicorn access/error logger juga diarahkan ke handler yang sama agar
    seluruh output aplikasi konsisten berformat JSON.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Samakan logger uvicorn dengan root agar tidak ada output non-JSON ganda.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
