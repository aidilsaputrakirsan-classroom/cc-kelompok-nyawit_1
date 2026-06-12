# Operations Guide - SiCure Procurement System

Panduan ini berisi langkah operasional untuk menjalankan, memantau, dan menangani masalah pada deployment microservices SiCure Procurement System.

## 1. Tujuan Dokumen

Dokumen ini mencakup:

- Cara menjalankan service lokal dan container deployment.
- Cara melakukan health check pada setiap service.
- Cara membaca log service.
- Cara memeriksa endpoint metrics.
- Cara melakukan troubleshooting umum.
- Jalur eskalasi ketika terjadi gangguan.
- Checklist operasional sistem.

---

## 2. Service Topology

| Service | Container | Internal Port | Public Access |
|----------|----------|----------|----------|
| Gateway | `gateway` | 80 | `http://localhost` |
| Auth Service | `auth-service` | 8001 | `/api/v1/auth/*` |
| Procurement Service | `procurement-service` | 8002 | `/api/v1/requisitions/*`, `/purchase-orders/*`, `/grn/*` |
| Auth Database | `auth-db` | 5432 | `localhost:5433` |
| Procurement Database | `procurement-db` | 5432 | `localhost:5434` |

---

## 3. Environment Setup

1. Salin file `.env.example` menjadi `.env`.

```bash
cp .env.example .env
```

2. Sesuaikan seluruh konfigurasi environment.

Contoh konfigurasi utama:

```env
APP_ENV=development

AUTH_DB_URL=postgresql://user:password@auth-db:5432/auth_db

PROCUREMENT_DB_URL=postgresql://user:password@procurement-db:5432/procurement_db

JWT_SECRET_KEY=your-secret-key

AUTH_SERVICE_URL=http://auth-service:8001
```

3. Jangan melakukan commit file `.env` ke repository.

4. Gunakan secret key yang kuat.

Generate secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 4. Menjalankan Sistem

Build seluruh image:

```bash
docker compose build
```

Menjalankan seluruh service:

```bash
docker compose up -d
```

Menjalankan ulang dengan rebuild:

```bash
docker compose up --build -d
```

Melihat status container:

```bash
docker compose ps
```

Menghentikan seluruh service:

```bash
docker compose down
```

Menghapus volume:

```bash
docker compose down -v
```

---

## 5. Health Checks

Gateway:

```bash
curl http://localhost/health
```

Auth Service:

```bash
curl http://localhost:8001/health
```

Procurement Service:

```bash
curl http://localhost:8002/health
```

Expected result:

```json
{
  "status": "healthy"
}
```

Seluruh endpoint harus mengembalikan HTTP Status Code `200`.

---

## 6. Logs

Melihat seluruh log:

```bash
docker compose logs
```

Melihat log Gateway:

```bash
docker compose logs -f gateway
```

Melihat log Auth Service:

```bash
docker compose logs -f auth-service
```

Melihat log Procurement Service:

```bash
docker compose logs -f procurement-service
```

Melihat log Auth Database:

```bash
docker compose logs -f auth-db
```

Melihat log Procurement Database:

```bash
docker compose logs -f procurement-db
```

Menampilkan 50 log terakhir:

```bash
docker compose logs --tail=50 procurement-service
```

---

## 7. Metrics

Auth Service:

```bash
curl http://localhost:8001/metrics
```

Procurement Service:

```bash
curl http://localhost:8002/metrics
```

Melalui Gateway:

```bash
curl http://localhost/api/v1/auth/metrics
```

Jika endpoint metrics belum tersedia, service dapat mengembalikan:

```text
404 Not Found
```

---

## 8. Procurement Workflow Verification

Verifikasi alur procurement:

```text
Requester
    ↓
Create Purchase Requisition
    ↓
SUBMITTED
    ↓
Admin Review
    ↓
APPROVED / REJECTED
    ↓
Purchase Order Issued
    ↓
PO_ISSUED
    ↓
Requester Upload GRN
    ↓
DOC_SUBMITTED
    ↓
Admin Verification
    ↓
VERIFIED
    ↓
CLOSED
```

Pastikan setiap perubahan status berjalan sesuai workflow di atas.

---

## 9. Common Troubleshooting

| Gejala | Cek | Solusi |
|----------|----------|----------|
| Gateway mengembalikan `502 Bad Gateway` | `docker compose logs gateway` | Pastikan Auth Service dan Procurement Service berjalan normal |
| Service gagal start | `docker compose logs <service>` | Periksa konfigurasi `.env` dan koneksi database |
| Database tidak dapat diakses | `docker compose logs auth-db` atau `procurement-db` | Pastikan container database berstatus healthy |
| Login gagal | `docker compose logs auth-service` | Periksa JWT Secret dan konfigurasi Auth Service |
| Upload GRN gagal | `docker compose logs procurement-service` | Periksa ukuran file dan tipe file yang diunggah |
| Inter-service authentication gagal | Procurement Service logs | Pastikan `AUTH_SERVICE_URL` mengarah ke Auth Service |
| Data tidak berubah setelah update kode | Docker menggunakan image lama | Jalankan rebuild dengan `docker compose up --build -d` |
| Swagger Docs tidak dapat diakses | Service belum siap | Periksa status container dan health check |

---

## 10. Escalation Path

| Masalah | Eskalasi ke |
|----------|----------|
| Endpoint Auth Service bermasalah | Lead Backend |
| Endpoint Procurement Service bermasalah | Lead Backend |
| Error UI atau Frontend | Lead Frontend |
| Error Docker, Deployment, Gateway, atau CI/CD | Lead DevOps |
| Dokumentasi, Pengujian, dan Monitoring | Lead QA & Docs |

Alur eskalasi:

1. Lead QA & Docs melakukan pengecekan awal menggunakan health check dan logs.
2. Jika masalah berasal dari backend, laporkan ke Lead Backend dengan bukti endpoint dan log error.
3. Jika masalah berasal dari frontend, laporkan ke Lead Frontend.
4. Jika masalah berasal dari Docker, Gateway, Railway, atau deployment, laporkan ke Lead DevOps.
5. Setelah perbaikan selesai, Lead QA & Docs melakukan verifikasi ulang.

---

## 11. Checklist Operasional

- [ ] Semua container berjalan dengan `docker compose ps`.
- [ ] Auth Service menunjukkan status healthy.
- [ ] Procurement Service menunjukkan status healthy.
- [ ] Gateway dapat diakses melalui `http://localhost/health`.
- [ ] Frontend dapat diakses melalui `http://localhost:5173`.
- [ ] Log service dapat dibaca menggunakan `docker compose logs`.
- [ ] Auth Database berstatus healthy.
- [ ] Procurement Database berstatus healthy.
- [ ] Endpoint API dapat diakses melalui Gateway.
- [ ] Purchase Requisition dapat dibuat.
- [ ] Purchase Order dapat diterbitkan.
- [ ] Upload dokumen GRN berjalan normal.
- [ ] Tidak ada error koneksi database.
- [ ] Tidak ada error `502 Bad Gateway`.
---

## 12. Conclusion

Dengan mengikuti panduan operasional ini, tim dapat menjalankan, memantau, dan melakukan troubleshooting terhadap seluruh komponen SiCure Procurement System secara konsisten baik pada lingkungan development maupun deployment berbasis container.