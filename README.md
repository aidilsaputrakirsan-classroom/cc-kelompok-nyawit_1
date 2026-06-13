# ☁️ SiCure — Sistem Informasi Procurement

![CI Pipeline](https://github.com/aidilsaputrakirsan-classroom/cc-kelompok-nyawit_1/actions/workflows/ci.yml/badge.svg)

SiCure (Sistem Informasi Procurement) adalah aplikasi berbasis cloud untuk mengelola
proses pengadaan barang/jasa secara digital, terstruktur, dan transparan — mulai dari
pengajuan permintaan, perbandingan penawaran vendor, persetujuan, penerbitan PO,
hingga verifikasi penerimaan barang.

**Backend:** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL
**Frontend:** React 19 + TypeScript + Vite
**Infra:** Docker Compose (lokal) · Railway (produksi)

---

## ⚡ Quick Start (Docker — cara tercepat)

Hanya butuh **Docker** + **Docker Compose**. Tidak perlu install Python/Node/PostgreSQL.

```bash
# 1. Clone repo
git clone https://github.com/aidilsaputrakirsan-classroom/cc-kelompok-nyawit_1.git
cd cc-kelompok-nyawit_1

# 2. Siapkan environment (nilai default sudah cukup untuk lokal)
cp .env.example .env

# 3. Seed data demo HANYA untuk first run, lalu jalankan semuanya
SEED_ON_STARTUP=true docker compose up -d --build

# (jalankan berikutnya cukup: docker compose up -d)
```

Atau pakai **Makefile** (lebih singkat):

```bash
make up      # build + start backend, frontend, postgres
make seed    # isi data demo (sekali saja saat pertama)
make logs    # lihat log
make down    # stop
```

Setelah container jalan:

| Layanan | URL |
|---------|-----|
| 🖥️ Frontend (web) | http://localhost:5173 |
| 🔌 Backend API | http://localhost:8000 |
| 📚 API Docs (Swagger) | http://localhost:8000/docs |
| ❤️ Health check | http://localhost:8000/api/v1/health |

Login dengan akun demo di bawah, dan aplikasi siap dipakai. Selesai. 🎉

> **Catatan seeding:** `SEED_ON_STARTUP=true` cukup dijalankan **sekali** untuk membuat
> akun demo + contoh PR di semua tahap. Untuk run berikutnya gunakan `docker compose up -d`
> biasa agar data tidak di-seed ulang. Migrasi database (`alembic upgrade head`) selalu
> berjalan otomatis di setiap startup.

---

## 🔐 Akun Demo

Tersedia setelah seeding (`make seed` atau `SEED_ON_STARTUP=true`):

| Email | Password | Role | Keterangan |
|-------|----------|------|------------|
| `admin@sicure.com` | `admin1234` | Admin | Review PR, terbitkan PO, verifikasi GRN |
| `requester1@sicure.com` | `requester1234` | Requester | Andi Kurniawan |
| `requester2@sicure.com` | `requester1234` | Requester | Dewi Lestari |
| `requester3@sicure.com` | `requester1234` | Requester | Rizky Pratama |

Seeder juga membuat **13 contoh Purchase Requisition** yang tersebar di seluruh tahap
status (SUBMITTED, APPROVED, REJECTED, PO_ISSUED, DOC_SUBMITTED, VERIFIED, CLOSED),
lengkap dengan penawaran vendor — sehingga demo bisa langsung menelusuri setiap alur
tanpa input manual.

---

## 👥 Tim

| Nama | NIM | Peran |
|------|------|--------|
| Muchlis Wahyu Saputra | 10231054 | Lead Backend |
| Ranaya Chintya Mahitsa | 10231078 | Lead Frontend |
| Andi Adam Firdaus | 10211014 | Lead DevOps |
| Ahmad Baihaqi | 10221063 | Lead DevOps |
| Az-Zahra Atikah Nurhaliza | 10231022 | Lead QA & Docs |

---

## 📌 Fitur Utama

- **Purchase Requisition (PR)** — pengajuan permintaan pengadaan beserta line items.
- **Perbandingan Penawaran Vendor (3-quotation)** — setiap PR menyertakan penawaran
  vendor + bukti survei. Jumlah vendor minimal mengikuti ambang nilai PR.
- **Approval + Penerbitan PO** — admin menyetujui PR dan menerbitkan Purchase Order
  untuk vendor terpilih dalam satu langkah.
- **GRN (Goods Receipt Note)** — requester mengunggah bukti penerimaan barang.
- **Verifikasi & Penutupan** — admin memverifikasi GRN lalu menutup pengadaan.
- **Role-Based Access Control** — hak akses Admin vs Requester.
- **JWT Auth** — access + refresh token, dengan logout (token revocation).
- **Audit & Tracking** — pemantauan status di setiap tahap.

---

## 🔄 Alur Procurement

```
┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 1. PR +    │──>│ 2. Approve   │──>│ 3. GRN        │──>│ 4. Verify     │
│ Vendor     │   │  + Issue PO  │   │  Submission   │   │  & Close      │
│ Quotes     │   │              │   │               │   │               │
└────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
  Requester        Admin              Requester          Admin

Status: SUBMITTED ─> PO_ISSUED ─> DOC_SUBMITTED ─> VERIFIED ─> CLOSED
                └─> REJECTED
```

1. **PR + Vendor Quotes (Requester).** Requester membuat PR (judul, justifikasi,
   line items) dan melampirkan penawaran vendor beserta bukti survei. Total dihitung
   otomatis; status awal `SUBMITTED`.
2. **Approve + Issue PO (Admin).** Admin me-review PR. Jika **APPROVE**, sistem langsung
   menerbitkan PO untuk vendor terpilih (default vendor rekomendasi, bisa di-override)
   dan status menjadi `PO_ISSUED`. Jika **REJECT**, status `REJECTED` (requester bisa
   merevisi & mengajukan ulang).
3. **GRN Submission (Requester).** Setelah barang diterima, requester mengunggah
   *commercial invoice* + foto barang. Status `DOC_SUBMITTED`.
4. **Verify & Close (Admin).** Admin memverifikasi (`VERIFIED`) lalu menutup pengadaan
   (`CLOSED`). Admin juga bisa mengembalikan GRN (`return`) ke requester untuk diperbaiki.

### Aturan Penawaran Vendor

| Nilai total PR | Minimal vendor | Rekomendasi |
|----------------|----------------|-------------|
| ≤ Rp5.000.000 (ambang) | 1 vendor | tepat 1 ditandai rekomendasi |
| > Rp5.000.000 | 3 vendor | tepat 1 ditandai rekomendasi |

- Ambang diatur via `QUOTE_THRESHOLD` (default `5000000`).
- Setiap vendor wajib menyertakan berkas bukti survei (JPG/PNG/PDF, maks 5MB).
- `allocated_budget` PO = harga vendor terpilih (bukan estimasi total PR).

---

## 🧰 Perintah Docker yang Sering Dipakai

```bash
docker compose up -d              # start (pakai image yang ada)
docker compose up -d --build      # start + rebuild image
docker compose logs -f backend    # log backend saja
docker compose exec backend python -m app.seed   # seed manual (idempotent)
docker compose down               # stop & hapus container
docker compose down -v            # stop + hapus volume (DATA DB HILANG)
```

Re-seed data demo dari awal (menghapus data demo lama lalu membuat ulang):

```bash
docker compose exec -e FORCE_SEED=true backend python -m app.seed
```

---

## 🛠️ Setup Manual (tanpa Docker)

Alternatif bila ingin menjalankan langsung di host. Butuh **Python 3.11+**,
**Node.js 20+**, dan **PostgreSQL 16+**.

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # lalu sesuaikan DATABASE_URL & JWT secrets
createdb sicure_db                  # buat database PostgreSQL

alembic upgrade head                # migrasi
python -m app.seed                  # seed user + data demo

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`DATABASE_URL` untuk koneksi lokal, contoh:
`postgresql+asyncpg://postgres:postgres@localhost:5432/sicure_db`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env                # default: VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run dev                         # http://localhost:5173
```

---

## 🔌 API Endpoints

Base URL: `http://localhost:8000/api/v1` · Dokumentasi interaktif: `/docs`

### Auth
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| POST | `/auth/register` | Admin | Buat user baru (role apa pun) |
| POST | `/auth/register-requester` | Public | Registrasi mandiri sebagai requester |
| POST | `/auth/login` | Public | Login → access + refresh token |
| POST | `/auth/refresh` | Public | Tukar refresh token (rotation) |
| POST | `/auth/logout` | Auth | Revoke access token |
| GET | `/auth/me` | Auth | Profil user saat ini |

### Requisitions (Requester)
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| POST | `/requisitions/` | Auth | Buat PR + vendor quotes (multipart) |
| GET | `/requisitions/` | Auth | List PR milik sendiri (paginasi + filter) |
| GET | `/requisitions/{id}` | Auth | Detail PR milik sendiri |
| PUT | `/requisitions/{id}` | Auth | Edit PR `SUBMITTED`/`REJECTED` (resubmit) |
| DELETE | `/requisitions/{id}` | Auth | Batalkan PR `SUBMITTED`/`REJECTED` |
| GET | `/requisitions/categories` | Auth | Kategori unik dari nama item |

### Requisitions (Admin)
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/requisitions/admin/` | Admin | List semua PR (paginasi + filter) |
| GET | `/requisitions/admin/{id}` | Admin | Detail PR mana pun |
| PUT | `/requisitions/admin/{id}/review` | Admin | APPROVE (+ terbitkan PO) / REJECT |

### Purchase Orders
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/purchase-orders/` | Admin | List semua PO |
| GET | `/purchase-orders/{po_id}` | Admin | Detail PO |
| GET | `/purchase-orders/by-pr/{pr_id}` | Admin | PO berdasarkan PR |
| GET | `/purchase-orders/{pr_id}/my-po` | Auth | PO untuk PR milik sendiri |

### GRN
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| POST | `/grn/{po_id}/submit-doc` | Auth | Upload invoice + foto barang |
| GET | `/grn/{grn_id}` | Auth | Detail GRN |
| GET | `/grn/by-po/{po_id}` | Auth | GRN berdasarkan PO |
| PUT | `/grn/admin/{grn_id}/verify` | Admin | Verifikasi (VERIFIED) / tutup (CLOSED) |
| PUT | `/grn/admin/{grn_id}/return` | Admin | Kembalikan GRN untuk diperbaiki |

### Lain-lain
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/health` & `/api/v1/health` | Public | Health check |

---

## 🧪 Testing

```bash
# Backend (pytest + coverage + property-based tests)
cd backend && pytest

# Atau di dalam container
docker compose exec backend pytest

# Frontend (vitest)
cd frontend && npm test
```

CI (`.github/workflows/ci.yml`) menjalankan test backend, test + build frontend,
dan build image Docker pada setiap push/PR ke `main`.

---

## 🔄 CI/CD Pipeline

Pipeline CI (`.github/workflows/ci.yml`) berjalan otomatis pada setiap **push** dan
**Pull Request** ke branch `main`.

### Jobs

- 🐍 **Test Backend** — `pytest` + coverage (gagal bila coverage < 40%).
- ⚛️ **Test Frontend** — `vitest` + build Vite.
- 🐳 **Build Docker** — build image backend & frontend (hanya jalan bila kedua test lulus).

### Alur

```text
Push / PR ke main
        │
        ▼
   GitHub Actions
        ├── 🐍 Test Backend  (pytest + coverage)
        ├── ⚛️ Test Frontend (vitest + build)
        └── 🐳 Build Docker  (butuh kedua test PASS)
```

Deployment ke Railway berjalan otomatis melalui integrasi GitHub–Railway setiap ada
merge ke `main` (di luar workflow CI di atas).

---

## 🚀 Deployment (Railway)

Aplikasi di-deploy sebagai **monolith** ke [Railway](https://railway.app):
1 backend service + 1 frontend service + 1 PostgreSQL dalam satu project.
Auto-deploy setiap push/merge ke `main`.

📖 Panduan lengkap (langkah dashboard, environment variables, troubleshooting):
**[docs/railway-deployment.md](docs/railway-deployment.md)**

| Service | URL |
|---------|-----|
| Frontend | https://sicure-app.up.railway.app |
| Backend API | https://sicure-api.up.railway.app |
| API Docs (Swagger) | https://sicure-api.up.railway.app/docs |

---

## 🗂️ Struktur Project

```
cc-kelompok-nyawit_1/
├── docker-compose.yml            # Orkestrasi: backend + frontend + postgres
├── docker-compose.override.yml   # Override dev (hot-reload, auto-seed)
├── docker-compose.prod.yml       # Override produksi
├── Makefile                      # Shortcut: make up/down/seed/logs
├── .env.example                  # Template environment (root, untuk Docker)
│
├── backend/                      # FastAPI + SQLAlchemy (async)
│   ├── Dockerfile
│   ├── alembic/                  # Migrasi database
│   ├── requirements.txt
│   └── app/
│       ├── main.py               # FastAPI app + middleware + health
│       ├── seed.py               # Seeder data demo (idempotent)
│       ├── core/                 # config, security (JWT/bcrypt), deps
│       ├── db/                   # engine + session async
│       ├── models/               # User, PR, LineItem, VendorQuote, PO, GRN
│       ├── schemas/              # Pydantic request/response
│       ├── routers/              # auth, requisitions(+admin), PO, grn(+admin)
│       ├── services/             # aturan bisnis vendor quote
│       └── utils/                # validasi & penyimpanan upload
│
├── frontend/                     # React 19 + TypeScript + Vite
│   ├── Dockerfile / Dockerfile.dev
│   └── src/                      # pages, components, contexts, services
│
├── docker/                       # Dokumentasi & script Docker
└── docs/                         # Dokumentasi proyek (lihat di bawah)
```

---

## 📚 Dokumentasi

- [Panduan Deploy Railway](docs/railway-deployment.md)
- [Arsitektur Docker](docs/architecture/docker-architecture.md)
- [Perbandingan Ukuran Image](docs/architecture/image-comparison.md)
- [Panduan Testing](docs/testing/testing-guide.md)
- [Hasil Test API (Swagger)](docs/testing/api-test-result.md)
- [Hasil UI Testing](docs/testing/ui-test-results.md)
- [Git Workflow](docs/guides/git-workflow.md)

---

## 🔒 Catatan Keamanan

1. **JWT Secret** — ganti `JWT_SECRET` & `JWT_REFRESH_SECRET` dengan string acak kuat
   sebelum produksi: `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
2. **CORS** — di produksi set `ALLOWED_ORIGINS` hanya ke domain frontend (tanpa wildcard).
3. **APP_ENV=production** — mengaktifkan pembatasan ukuran request body & CORS ketat.
4. **File Upload** — hanya JPG/PNG/PDF, maks 5MB/file; nama file di-sanitize + UUID prefix.
5. **Password** — di-hash dengan bcrypt; tidak pernah disimpan plaintext.
6. **Database** — gunakan kredensial kuat di produksi; jangan pakai user default tanpa password.

---

## 🧱 Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Axios |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| Database | PostgreSQL 16 (asyncpg) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Migration | Alembic |
| Infra | Docker Compose, Railway |

---

## 📄 License

Internal project — Universitas.
