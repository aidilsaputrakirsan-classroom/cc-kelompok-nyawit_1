# ============================================================
# Stage 1 — Builder: install dependencies (with build tools)
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Build deps hanya dibutuhkan saat compile wheel (tidak ikut ke image akhir).
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dulu → layer caching: pip install hanya re-run bila
# requirements.txt berubah, bukan setiap kali kode berubah.
COPY backend/requirements.txt .

# Install ke prefix terpisah agar mudah disalin ke stage runtime.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================
# Stage 2 — Runtime: image ramping tanpa build tools
# ============================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime deps: curl untuk healthcheck. (asyncpg tidak butuh libpq.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Salin dependency yang sudah ter-install dari stage builder.
COPY --from=builder /install /usr/local

# Copy application code.
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini .

# Buat user non-root + folder uploads dengan kepemilikan yang benar
# (best practice keamanan — container tidak berjalan sebagai root).
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app
USER appuser

# Expose port (informational — Railway inject $PORT saat runtime)
EXPOSE 8000

# Health check (pakai $PORT bila ada, fallback 8000 untuk lokal)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Migrasi SELALU jalan saat startup (wajib untuk update schema).
# Seeding OPSIONAL — dikontrol env SEED_ON_STARTUP (default: false).
CMD ["sh", "-c", "echo '🔄 Running database migrations...' && alembic upgrade head && echo '✅ Migrations completed' && if [ \"$SEED_ON_STARTUP\" = \"true\" ]; then echo '🌱 Running seed data...' && python -m app.seed; fi && echo '🚀 Starting application...' && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
