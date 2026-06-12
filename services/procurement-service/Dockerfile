# Procurement Service Dockerfile
# Berisi kode procurement saja — TIDAK ada kode auth di sini.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Buat folder uploads
RUN mkdir -p /app/uploads

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
