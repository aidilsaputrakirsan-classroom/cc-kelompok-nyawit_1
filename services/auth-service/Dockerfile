# Auth Service Dockerfile
# Service ini HANYA berisi kode auth — tidak ada kode procurement di sini.
# Ini yang membuat image-nya kecil dan deploy-nya cepat.

FROM python:3.12-slim

WORKDIR /app

# Install dependencies dulu (layer caching — kalau requirements tidak berubah,
# Docker tidak perlu install ulang)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Auth Service jalan di port 8001
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
