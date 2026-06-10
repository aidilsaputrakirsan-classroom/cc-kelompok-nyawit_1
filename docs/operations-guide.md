# Panduan Operasional Sistem — SiCure

Dokumen ini merupakan panduan operasional harian untuk tim pengembang dan pengelola sistem **SiCure (Sistem Information Procurement)**. Panduan ini mencakup cara memeriksa kesehatan sistem, membaca log, melacak request, memantau metrik, menangani masalah umum, dan jalur eskalasi ketika terjadi gangguan.

---

## 1. Cara Memeriksa Kesehatan Sistem (Health Check)

Health check digunakan untuk memastikan seluruh service berjalan normal sebelum dan sesudah deployment, atau kapanpun dicurigai ada gangguan.

### 1.1 Pengecekan Cepat via Terminal

```bash
# Cek status semua container sekaligus
docker compose ps

# Cek Gateway (pintu masuk utama sistem)
curl -s http://localhost/health | python3 -m json.tool

# Cek Auth Service
curl -s http://localhost/auth/health | python3 -m json.tool

# Cek Procurement Service (sekaligus melihat status Circuit Breaker)
curl -s http://localhost/procurement/health | python3 -m json.tool
```

### 1.2 Interpretasi Respons Health Check

Contoh respons normal (sistem sehat):

```json
{
  "status": "healthy",
  "service": "procurement-service",
  "version": "2.0.0",
  "dependencies": {
    "auth-service": {
      "state": "CLOSED",
      "failure_count": 0
    },
    "database": {
      "status": "connected"
    }
  }
}
```

Panduan membaca nilai `status`:

| Nilai | Arti | Tindakan yang Diperlukan |
|-------|------|--------------------------|
| `healthy` | Semua service dan dependency normal | Tidak perlu tindakan |
| `degraded` | Auth Service bermasalah, Circuit Breaker OPEN | Monitor log, tunggu pemulihan otomatis |
| `unhealthy` | Database tidak dapat diakses | Segera periksa koneksi database |

### 1.3 Pengecekan via Browser (Status Page)

Buka browser dan akses halaman status dashboard:

```
http://localhost/status
```

Halaman ini menampilkan status real-time semua service dan akan otomatis refresh setiap 10 detik.

---

## 2. Cara Membaca Log

Log adalah catatan aktivitas sistem yang digunakan untuk mengetahui apa yang terjadi di dalam setiap service.

### 2.1 Melihat Log Per Service

```bash
# Log Auth Service — untuk masalah login, register, atau token
docker compose logs -f auth-service

# Log Procurement Service — untuk masalah requisition, PO, atau GRN
docker compose logs -f procurement-service

# Log API Gateway (Nginx) — untuk masalah routing atau koneksi
docker compose logs -f gateway

# Log Database Auth
docker compose logs -f auth-db

# Log Database Procurement
docker compose logs -f procurement-db
```

### 2.2 Opsi Berguna Saat Membaca Log

```bash
# Tampilkan 50 baris log terakhir tanpa follow
docker compose logs --tail=50 procurement-service

# Tampilkan log dari semua service sekaligus
docker compose logs -f auth-service procurement-service gateway

# Filter log berdasarkan kata kunci tertentu
docker compose logs procurement-service 2>&1 | grep "ERROR"

# Filter log hanya yang mengandung level WARNING ke atas
docker compose logs auth-service 2>&1 | grep -E '"level":"(WARNING|ERROR|CRITICAL)"'
```

### 2.3 Memahami Struktur Log JSON

SiCure menggunakan structured logging dalam format JSON. Setiap baris log memiliki struktur:

```json
{
  "timestamp": "2026-06-10T08:30:45.123Z",
  "level": "INFO",
  "service": "procurement-service",
  "correlation_id": "req-abc123",
  "method": "POST",
  "path": "/requisitions",
  "status_code": 201,
  "duration_ms": 87.5,
  "message": "POST /requisitions → 201 (87.5ms)"
}
```

Panduan membaca field log:

| Field | Keterangan |
|-------|------------|
| `timestamp` | Waktu kejadian dalam format UTC |
| `level` | Tingkat log: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `service` | Nama service yang menghasilkan log |
| `correlation_id` | ID unik untuk melacak satu request lintas service |
| `method` | HTTP method yang digunakan |
| `path` | Endpoint yang diakses |
| `status_code` | Kode HTTP respons |
| `duration_ms` | Durasi pemrosesan request dalam milidetik |

---

## 3. Cara Melacak Request (Correlation ID)

Correlation ID adalah kode unik yang disisipkan di setiap request dan diteruskan ke semua service yang terlibat. Dengan Correlation ID, kita bisa menelusuri perjalanan satu request dari gateway hingga database.

### 3.1 Mendapatkan Correlation ID

Setiap respons dari sistem menyertakan header `X-Correlation-ID`:

```bash
# Kirim request dan tampilkan header respons
curl -v -X GET http://localhost/procurement/requisitions \
  -H "Authorization: Bearer <token>" 2>&1 | grep -i "x-correlation-id"

# Contoh output:
# < X-Correlation-ID: req-a1b2c3d4
```

### 3.2 Melacak Request di Semua Service

Setelah mendapatkan Correlation ID, gunakan untuk filter log:

```bash
# Cari log dengan Correlation ID tertentu di semua service
docker compose logs auth-service procurement-service 2>&1 | grep "req-a1b2c3d4"
```

### 3.3 Contoh Hasil Pelacakan

Berikut contoh alur log satu request `POST /procurement/requisitions`:

```
[gateway]              req-a1b2c3d4 → diteruskan ke procurement-service
[procurement-service]  req-a1b2c3d4 POST /requisitions diterima
[procurement-service]  req-a1b2c3d4 → memanggil Auth Service untuk verifikasi token
[auth-service]         req-a1b2c3d4 GET /verify → 200 (12ms)
[procurement-service]  req-a1b2c3d4 Token valid, user_id=5
[procurement-service]  req-a1b2c3d4 POST /requisitions → 201 (95ms)
```

### 3.4 Menggunakan Script Bantu

```bash
# Jalankan script pelacak log
./scripts/logs.sh trace req-a1b2c3d4
```

---

## 4. Cara Memeriksa Metrik Sistem

Metrik digunakan untuk memantau performa dan beban kerja setiap service secara kuantitatif.

### 4.1 Mengambil Metrik via Terminal

```bash
# Metrik Auth Service
curl -s http://localhost/auth/metrics | python3 -m json.tool

# Metrik Procurement Service
curl -s http://localhost/procurement/metrics | python3 -m json.tool
```

### 4.2 Memahami Isi Metrik

Contoh respons metrik:

```json
{
  "service": "procurement-service",
  "uptime_seconds": 3600,
  "total_requests": 250,
  "total_errors": 3,
  "error_rate_percent": 1.2,
  "status_codes": {
    "200": 180,
    "201": 67,
    "401": 2,
    "503": 1
  },
  "latency": {
    "p50_ms": 45.2,
    "p95_ms": 210.5,
    "p99_ms": 380.1,
    "avg_ms": 67.8
  },
  "endpoints": {
    "GET /requisitions": {
      "count": 120,
      "errors": 0,
      "avg_latency_ms": 38.5
    },
    "POST /requisitions": {
      "count": 45,
      "errors": 1,
      "avg_latency_ms": 95.2
    }
  }
}
```

Panduan membaca nilai metrik:

| Metrik | Nilai Normal | Perlu Diwaspadai |
|--------|-------------|-----------------|
| `error_rate_percent` | < 1% | > 5% |
| `p95_ms` (latency) | < 500ms | > 1000ms |
| `uptime_seconds` | Terus bertambah | Tiba-tiba reset ke 0 |

### 4.3 Menggunakan Script Bantu

```bash
# Tampilkan semua metrik sekaligus
./scripts/logs.sh metrics
```

---

## 5. Penanganan Masalah Umum (Troubleshooting)

### 5.1 Tabel Masalah dan Solusi

| No | Gejala | Kemungkinan Penyebab | Langkah Penyelesaian |
|----|--------|---------------------|---------------------|
| 1 | Container tidak mau start | Port sudah dipakai aplikasi lain | Jalankan `docker compose down` lalu `docker compose up -d` |
| 2 | HTTP `502 Bad Gateway` | Service backend crash atau belum siap | Cek `docker compose ps`, restart service yang bermasalah |
| 3 | HTTP `401 Unauthorized` | Token tidak valid atau sudah kadaluarsa | Login ulang untuk mendapatkan token baru |
| 4 | HTTP `503` di endpoint procurement | Auth Service down atau Circuit Breaker OPEN | Cek `docker compose logs auth-service`, tunggu pemulihan otomatis |
| 5 | Error `CORS Blocked` di browser | Frontend mengakses API langsung ke port backend | Pastikan frontend menggunakan URL gateway `http://localhost/...` |
| 6 | Data tidak berubah setelah update kode | Docker masih menggunakan image lama | Jalankan `docker compose down -v && docker compose up --build -d` |
| 7 | Database tidak bisa diakses | Volume corrupt atau konfigurasi salah | Hapus volume: `docker compose down -v`, lalu build ulang |
| 8 | Login selalu gagal padahal password benar | `SECRET_KEY` berubah antar deployment | Pastikan `SECRET_KEY` di `.env` konsisten |

### 5.2 Langkah Diagnosis Umum

Gunakan urutan langkah berikut setiap kali terjadi gangguan:

```bash
# Langkah 1: Cek status semua container
docker compose ps

# Langkah 2: Cek health endpoint
curl -s http://localhost/health | python3 -m json.tool
curl -s http://localhost/procurement/health | python3 -m json.tool

# Langkah 3: Baca log service yang bermasalah
docker compose logs --tail=30 <nama-service>

# Langkah 4: Restart service yang bermasalah
docker compose restart <nama-service>

# Langkah 5: Jika masih bermasalah, rebuild ulang
docker compose down -v
docker compose up --build -d
```

---

## 6. Jalur Eskalasi (Escalation Path)

Ketika terjadi gangguan yang tidak dapat diselesaikan dengan panduan di atas, gunakan jalur eskalasi berikut:

### 6.1 Tingkat Eskalasi

| Tingkat | Kondisi | Penanggung Jawab | Tindakan |
|---------|---------|-----------------|----------|
| **Level 1** | Gangguan minor — satu endpoint tidak berfungsi | Lead QA & Docs | Cek log, coba solusi di Bagian 5 |
| **Level 2** | Gangguan sedang — satu service down | Lead Backend / Lead DevOps | Restart service, cek konfigurasi |
| **Level 3** | Gangguan berat — semua service tidak bisa diakses | Lead DevOps | Rebuild ulang seluruh stack |
| **Level 4** | Data hilang atau corrupt | Lead Backend + Lead DevOps | Restore dari backup, hubungi dosen/asdos |

### 6.2 Kontak Tim

| Peran | Nama | Tanggung Jawab Utama |
|-------|------|---------------------|
| Lead Backend | Muchlis Wahyu Saputra | Auth Service, Procurement Service, API |
| Lead Frontend | Ranaya Chintya Mahitsa | UI, status page, error handling |
| Lead DevOps | Andi Adam Firdaus | Docker, Gateway, deployment |
| Lead DevOps | Ahmad Baihaqi | CI/CD pipeline, monitoring |
| Lead QA & Docs | Az-Zahra Atikah Nurhaliza | Dokumentasi, pengujian, health check |

### 6.3 Checklist Sebelum Melaporkan ke Dosen/Asdos

Pastikan langkah berikut sudah dilakukan sebelum eskalasi ke dosen atau asisten dosen:

- [ ] Sudah menjalankan `docker compose ps` dan mendokumentasikan hasilnya
- [ ] Sudah membaca log service yang bermasalah (`docker compose logs`)
- [ ] Sudah mencoba restart service (`docker compose restart`)
- [ ] Sudah mencoba rebuild ulang (`docker compose down -v && docker compose up --build -d`)
- [ ] Sudah mendokumentasikan pesan error yang muncul
- [ ] Sudah mencatat langkah reproduksi masalah (cara memunculkan kembali error)