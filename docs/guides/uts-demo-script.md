# 🎤 UTS Demo Script — SICURE (Sistem Procurement)

⏱️ **Total waktu: ±15 menit**

---

## 1. 🖥️ Live Demo (±10 menit)

### ⏱️ Menit 0–1 — Setup (DevOps)

“Pertama, kami menjalankan aplikasi menggunakan Docker Compose.”

Langkah:
- Buka terminal di root project
- Jalankan:
```bash
docker compose up -d
```
- Lanjut:
```bash 
docker compose ps
```

Tunjukkan:
- Terdapat 3 service: database, backend, frontend
- Semua service dalam kondisi running
- Database sudah dalam kondisi healthy

---

### ⏱️ Menit 1–3 — Authentication (Frontend)

“Selanjutnya kami mendemonstrasikan proses autentikasi user.”

Buka aplikasi:
- http://localhost:3000

Langkah:
- Register user baru
- Tunjukkan validasi form (jika ada)
- Login menggunakan akun tersebut

Tunjukkan:
- User berhasil login
- Masuk ke halaman dashboard SICURE
- Akses dibatasi jika belum login (protected route)

---

### ⏱️ Menit 3–6 — CRUD Operations (Frontend + Backend)

“Berikutnya fitur utama sistem, yaitu pengelolaan data procurement.”

Langkah:
- Tambahkan 2–3 data pengadaan (Create)
- Tampilkan data pada tabel (Read)
- Gunakan fitur pencarian (Search)
- Edit salah satu data (Update)
- Hapus satu data (Delete)

Tunjukkan:
- Perubahan data langsung tersimpan di database
- Frontend terhubung dengan backend API

---

### ⏱️ Menit 6–7 — Backend Demo (Backend)

“Backend kami disediakan dalam bentuk REST API.”

Buka:
- http://localhost:8000/docs

Tunjukkan:
- Dokumentasi API (Swagger UI)
- Endpoint autentikasi dan procurement
- Endpoint `/health` untuk pengecekan sistem

Jelaskan singkat:
- Backend menggunakan FastAPI
- Dokumentasi API dibuat otomatis

---

### ⏱️ Menit 7–8 — Data Persistence (DevOps)

“Selanjutnya kami menguji penyimpanan data.”

Langkah:
```bash
docker compose down
docker compose up -d
```

- Login kembali

Tunjukkan:
- Data sebelumnya tetap tersedia

Jelaskan:
- Data disimpan menggunakan Docker volume

---

### ⏱️ Menit 8–10 — Docker Explanation (DevOps)

“Berikut konfigurasi Docker yang digunakan.”

Buka:
- `docker-compose.yml`

Jelaskan:
- Terdapat 3 service utama: db, backend, frontend
- `depends_on` untuk mengatur urutan service
- `healthcheck` untuk memastikan service siap digunakan
- Volume digunakan untuk penyimpanan data database

---

## 2. 💻 Code Walkthrough (±5 menit)

### ⏱️ Menit 0–2 — DevOps

Tunjukkan:
- `docker-compose.yml`

Jelaskan:
- Struktur service
- Konfigurasi network antar container
- Volume untuk persistensi data

---

### ⏱️ Menit 2–3 — Backend

Buka:
- `backend/Dockerfile`

Jelaskan:
- Base image yang digunakan (Python)
- Instalasi dependencies
- Proses build image

Tambahkan:
- Sistem autentikasi menggunakan JWT

---

### ⏱️ Menit 3–4 — Frontend

Buka:
- `frontend/Dockerfile`

Jelaskan:
- Multi-stage build
- Proses build aplikasi React
- Deployment menggunakan Nginx

---

### ⏱️ Menit 4–5 — Dokumentasi

Tunjukkan:
- `README.md`

Jelaskan:
- Cara menjalankan project
- Struktur folder
- Gambaran singkat sistem SICURE

---

## 3. 🎤 Individual Viva

Setiap anggota menjelaskan:
- Bagian yang dikerjakan
- Konsep yang digunakan (Docker, REST API, JWT, dll)