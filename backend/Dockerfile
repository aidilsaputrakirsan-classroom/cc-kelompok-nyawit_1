FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations and start server
# Migration ALWAYS runs on startup (required for schema updates)
# Seeding is OPTIONAL - controlled by SEED_ON_STARTUP environment variable
# Default: SEED_ON_STARTUP=false (recommended for development)
# Set SEED_ON_STARTUP=true only for first setup or when you want to seed data
CMD ["sh", "-c", "echo '🔄 Running database migrations...' && alembic upgrade head && echo '✅ Migrations completed' && if [ \"$SEED_ON_STARTUP\" = \"true\" ]; then echo '🌱 Running seed data...' && python -m app.seed; fi && echo '🚀 Starting application...' && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
