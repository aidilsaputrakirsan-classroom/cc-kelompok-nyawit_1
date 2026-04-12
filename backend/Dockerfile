# ============================================================
# Stage: Production Image
# ============================================================

# 1. Base image — Python 3.12 slim (debian minimal, ~50MB)
FROM python:3.12-slim

# Install curl for healthcheck, postgresql-client for pg_isready, and create non-root user
RUN apt-get update && apt-get install -y curl postgresql-client && rm -rf /var/lib/apt/lists/* && \
    useradd -m appuser

# 2. Set working directory di dalam container
WORKDIR /app

# 3. Copy HANYA requirements.txt dulu (cache optimization)
#    Layer ini hanya rebuild jika requirements.txt berubah
COPY requirements.txt .

# 4. Install Python dependencies
#    --no-cache-dir: jangan simpan pip cache (hemat space)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy seluruh kode aplikasi
#    Layer ini rebuild setiap kali kode berubah
COPY . .

# Ubah kepemilikan direktori app ke user appuser
RUN chown -R appuser:appuser /app

# Gunakan non-root user
USER appuser

# 6. Dokumentasikan port yang digunakan
EXPOSE 8000

# Buat healthcheck untuk mengecek status aplikasi
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

# 7. Command untuk menjalankan aplikasi
#    --host 0.0.0.0: agar bisa diakses dari luar container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
