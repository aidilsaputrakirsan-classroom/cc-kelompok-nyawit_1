# SiCure Operations Guide

## 1. Tujuan

Dokumen ini digunakan sebagai panduan operasional untuk menjalankan, memantau, dan melakukan troubleshooting sistem SiCure. Sistem terdiri dari Gateway Service, Auth Service, Procurement Service, Frontend, serta database PostgreSQL yang berjalan menggunakan Docker Compose.

---

## 2. Arsitektur Sistem

Komponen utama sistem:

* Gateway Service (Nginx)
* Auth Service
* Procurement Service
* Frontend
* Auth Database (PostgreSQL)
* Procurement Database (PostgreSQL)

### Deskripsi Komponen

| Service             | Fungsi                                                              |
| ------------------- | ------------------------------------------------------------------- |
| frontend            | Menyediakan antarmuka pengguna sistem SiCure                        |
| gateway             | Menjadi pintu masuk utama dan meneruskan request ke service terkait |
| auth-service        | Mengelola autentikasi dan otorisasi pengguna                        |
| procurement-service | Mengelola fitur procurement pada sistem                             |
| auth-db             | Database untuk Auth Service                                         |
| procurement-db      | Database untuk Procurement Service                                  |

---

## 3. Menjalankan Sistem

### Menjalankan Seluruh Service

```bash
docker compose up -d
```

### Menjalankan Ulang Service

```bash
docker compose restart
```

### Menghentikan Seluruh Service

```bash
docker compose down
```

### Melihat Status Service

```bash
docker compose ps
```

Status yang diharapkan:

| Service             | Status  |
| ------------------- | ------- |
| gateway             | Up      |
| frontend            | Up      |
| auth-service        | Healthy |
| procurement-service | Healthy |
| auth-db             | Healthy |
| procurement-db      | Healthy |

---

## 4. Health Check

Health check digunakan untuk memastikan setiap layanan berjalan dengan baik dan dapat menerima request.

### Gateway Service

```bash
curl http://localhost/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "gateway"
}
```

### Auth Service

```bash
curl http://localhost/auth/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "auth-service",
  "env": "development"
}
```

### Procurement Service

Health check Procurement Service berhasil terverifikasi melalui log container.

Contoh log:

```text
INFO: 127.0.0.1:50828 - "GET /health HTTP/1.1" 200 OK
```

Status HTTP 200 OK menunjukkan bahwa Procurement Service berjalan dengan baik dan dapat merespons permintaan health check.

---

## 5. Monitoring Log

Monitoring log digunakan untuk memantau aktivitas sistem, mendeteksi error, dan membantu proses troubleshooting.

### Melihat Log Auth Service

```bash
docker logs sicure-auth-service --tail 20
```

### Melihat Log Procurement Service

```bash
docker logs sicure-procurement-service --tail 20
```

### Melihat Log Gateway

```bash
docker logs sicure-gateway --tail 20
```

### Contoh Log Normal

```text
INFO: 172.18.0.7:57474 - "GET /api/v1/auth/health HTTP/1.1" 200 OK
INFO: 127.0.0.1:50828 - "GET /health HTTP/1.1" 200 OK
```

### Status Logging

Berdasarkan hasil pengujian, seluruh service menghasilkan log yang dapat dipantau menggunakan Docker logs. Log digunakan untuk memantau aktivitas service, status endpoint, dan membantu proses troubleshooting ketika terjadi error.

---

## 6. Monitoring Database

Pastikan database berjalan dengan status healthy.

```bash
docker compose ps
```

Status yang diharapkan:

* auth-db → healthy
* procurement-db → healthy

Jika status database tidak healthy, lakukan restart service terkait.

```bash
docker compose restart auth-db
docker compose restart procurement-db
```

---

## 7. Monitoring Metrics

Saat dilakukan pengujian, endpoint metrics belum tersedia pada sistem.

Contoh hasil pengujian:

```bash
curl http://localhost/auth/metrics
```

Response:

```json
{
  "detail": "Not Found"
}
```

Monitoring sistem saat ini dilakukan menggunakan:

* Health Check Endpoint
* Docker Container Status
* Docker Logs

---

## 8. Troubleshooting

### Gateway Tidak Dapat Diakses

Periksa status service:

```bash
docker compose ps
```

Periksa log gateway:

```bash
docker logs sicure-gateway
```

---

### Auth Service Tidak Merespon

Periksa health endpoint:

```bash
curl http://localhost/auth/health
```

Periksa log service:

```bash
docker logs sicure-auth-service
```

---

### Procurement Service Tidak Merespon

Periksa log service:

```bash
docker logs sicure-procurement-service
```

Pastikan container berstatus healthy:

```bash
docker compose ps
```

---

### Database Connection Error

Periksa status database:

```bash
docker compose ps
```

Restart database jika diperlukan:

```bash
docker compose restart auth-db
docker compose restart procurement-db
```

---

### Metrics Endpoint Tidak Tersedia

Gejala:

```json
{
  "detail": "Not Found"
}
```

Kemungkinan penyebab:

* Endpoint metrics belum diimplementasikan
* Route metrics belum dikonfigurasi
* Service belum diperbarui

Langkah pengecekan:

```bash
curl http://localhost/auth/metrics
```

Periksa log service terkait:

```bash
docker logs sicure-auth-service
docker logs sicure-procurement-service
```

---

## 9. Escalation Path

Jika ditemukan masalah yang tidak dapat diselesaikan melalui langkah troubleshooting, lakukan eskalasi sesuai tanggung jawab tim.

| Permasalahan                                                  | Eskalasi       |
| ------------------------------------------------------------- | -------------- |
| Error endpoint atau API                                       | Lead Backend   |
| Error frontend atau tampilan aplikasi                         | Lead Frontend  |
| Error Docker, gateway, deployment, atau konfigurasi container | Lead DevOps    |
| Dokumentasi, pengujian, dan monitoring                        | Lead QA & Docs |

### Alur Penanganan

1. Lead QA & Docs melakukan pengecekan awal menggunakan health check dan log monitoring.
2. Identifikasi sumber masalah berdasarkan service yang terdampak.
3. Laporkan temuan beserta bukti log atau hasil pengujian kepada penanggung jawab terkait.
4. Setelah perbaikan dilakukan, lakukan verifikasi ulang sebelum sistem dinyatakan normal.

---

## 10. Monitoring Checklist

Lakukan pengecekan berikut sebelum sistem digunakan:

* [ ] Gateway Service berjalan
* [ ] Frontend berjalan
* [ ] Auth Service healthy
* [ ] Procurement Service healthy
* [ ] Auth Database healthy
* [ ] Procurement Database healthy
* [ ] Endpoint health dapat diakses
* [ ] Tidak terdapat error kritis pada log
* [ ] Sistem dapat diakses melalui gateway
* [ ] Status container menunjukkan kondisi healthy

---

## 11. Hasil Verifikasi Monitoring

Berdasarkan pengujian yang telah dilakukan:

| Komponen             | Status         |
| -------------------- | -------------- |
| Gateway Service      | Healthy        |
| Auth Service         | Healthy        |
| Procurement Service  | Healthy        |
| Auth Database        | Healthy        |
| Procurement Database | Healthy        |
| Docker Logs          | Berfungsi      |
| Metrics Endpoint     | Belum tersedia |

Monitoring saat ini dilakukan melalui health check endpoint, status container Docker, dan log service.

---

## 12. Kesimpulan

Berdasarkan hasil pengujian operasional:

* Gateway Service berjalan dengan baik.
* Auth Service berjalan dengan baik.
* Procurement Service berjalan dengan baik.
* Database berada pada kondisi healthy.
* Monitoring dapat dilakukan melalui health endpoint dan Docker logs.
* Endpoint metrics belum tersedia sehingga observability masih berfokus pada health check dan log monitoring.
* Sistem siap digunakan untuk kebutuhan pengembangan dan pengujian lebih lanjut.
