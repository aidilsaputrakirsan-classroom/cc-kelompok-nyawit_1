# Release Notes — Milestone 2

> Dokumen ini berisi rangkuman pengembangan aplikasi **SiCure (Sistem Information Procurement)** pada Milestone 2 yang berfokus pada implementasi *Continuous Integration* dan *Continuous Deployment* (CI/CD). Pada fase ini, aplikasi telah berhasil di-*deploy* ke server cloud dan terhubung dengan pipeline otomatis berbasis GitHub Actions.

---

## Deployment dan Infrastruktur Cloud

Pipeline CI/CD pada proyek ini dijalankan menggunakan GitHub Actions untuk proses otomatisasi pengujian dan workflow pengembangan aplikasi.

Setiap perubahan kode yang dikirim ke branch utama akan secara otomatis melalui proses:
1. Validasi source code
2. Proses build aplikasi
3. Pengujian otomatis (*automated testing*)
4. Deployment ke server production

Dengan implementasi ini, proses distribusi aplikasi menjadi lebih cepat, konsisten, dan meminimalkan kesalahan manual saat deployment.

---

## 🌐 Production URLs

| Layanan | URL |
|---------|-----|
| Frontend | `[TANYA ANDI/BAIHAQI — URL production]` |
| Backend API | `[TANYA ANDI/BAIHAQI — URL backend]` |
| API Docs (Swagger) | `[TANYA ANDI/BAIHAQI — URL/docs]` |

---

## 🆕 Fitur Utama yang Tersedia

### 1. Sistem Autentikasi Pengguna
Aplikasi telah mendukung fitur autentikasi berbasis JSON Web Token (JWT), meliputi:
- Registrasi akun pengguna baru
- Login pengguna
- Validasi token autentikasi
- Penyimpanan token di browser

### 2. Manajemen Data Procurement (CRUD)
Pengguna dapat melakukan pengelolaan data secara langsung melalui dashboard aplikasi, meliputi:
- Menambahkan data
- Melihat daftar data
- Mengubah data
- Menghapus data

Seluruh proses telah terhubung dengan database PostgreSQL pada server production.

### 3. [TANYA MUCHLIS — Apakah ada fitur tambahan lain?]
> *Contoh: integrasi pihak ketiga, notifikasi, laporan, dsb. Isi atau hapus bagian ini.*

---

## 🛠️ Tech Stack

| Komponen | Teknologi | Versi |
|----------|-----------|-------|
| Backend | FastAPI | ≥ 0.110.0 |
| Backend Runtime | Uvicorn | ≥ 0.29.0 |
| Database ORM | SQLAlchemy (async) | ≥ 2.0.0 |
| Database Driver | asyncpg | ≥ 0.29.0 |
| Migrasi Database | Alembic | ≥ 1.13.0 |
| Autentikasi | PyJWT + passlib bcrypt | ≥ 2.8.0 |
| Frontend | React + TypeScript | ^19.2.4 |
| Frontend Build | Vite | ^8.0.4 |
| Frontend Router | React Router DOM | ^7.14.1 |
| HTTP Client | Axios | ^1.15.0 |
| Database Production | PostgreSQL | 16 |
| Database Testing | SQLite (in-memory) | — |
| Container | Docker + Docker Compose | — |
| Testing Backend | pytest + pytest-asyncio + httpx | ≥ 8.0.0 |
| Testing Frontend | Vitest + Testing Library | — |
| CI/CD | GitHub Actions | — |
| Cloud Deployment | [TANYA ANDI — Railway / Server Asdos?] | — |

---

## 🔄 Implementasi CI/CD

Pipeline CI/CD pada proyek ini menggunakan GitHub Actions untuk membantu proses otomatisasi pengembangan dan deployment aplikasi.

Pipeline otomatis mencakup:
- Linting source code
- Automated testing menggunakan pytest (backend) dan Vitest (frontend)
- Build Docker image
- Deployment ke server production

Dengan sistem ini, setiap update kode dapat langsung diuji dan dipublikasikan secara otomatis tanpa perlu deployment manual.

---

## ✅ Hasil Deployment

- Frontend berhasil berjalan di environment production
- Backend API aktif dan dapat diakses publik
- Database PostgreSQL berhasil terhubung
- Pipeline GitHub Actions berhasil menjalankan workflow otomatis
- Aplikasi dapat diakses secara publik melalui domain live demo

---

## 📊 Statistik Milestone 2

| Metrik | Jumlah |
|--------|--------|
| Unit test backend | ≥ 12 test |
| Unit test frontend | ≥ 7 test |
| CI pipeline jobs | 4 jobs |
| PR yang di-merge | [Cek di GitHub] |
| Total commit | [Cek di GitHub] |

---

## 🗺️ Roadmap Update

| Minggu | Target | Status |
|--------|--------|--------|
| 1 | Setup & Hello World | ✅ |
| 2 | REST API + Database | ✅ |
| 3 | React Frontend | ✅ |
| 4 | Full-Stack + Auth | ✅ |
| 5–7 | Docker & Compose | ✅ |
| 8 | UTS Demo (Milestone 1) | ✅ |
| 9 | Git Workflow & Branching | ✅ |
| 10 | CI Pipeline & Automated Testing | ✅ |
| 11 | CD Pipeline & Cloud Deployment | ✅ |
| 12–14 | Microservices & Monitoring | ⬜ |
| 15 | Final Polish & Security | ⬜ |
| 16 | UAS Demo (Milestone 3) | ⬜ |

---

## 🐛 Known Issues

- [TANYA TIM — ada masalah yang belum terselesaikan? Kalau tidak ada, hapus baris ini dan tulis "Tidak ada known issues saat ini"]

---

## 👥 Kontribusi Tim

| Nama | NIM | Peran | Kontribusi Utama |
|------|-----|-------|-----------------|
| Muchlis Wahyu Saputra | 10231054 | Lead Backend | pytest, unit test backend, health endpoint |
| Ranaya Chintya Mahitsa | 10231078 | Lead Frontend | Vitest, unit test frontend, UI components |
| Andi Adam Firdaus | 10211014 | Lead DevOps | GitHub Actions CI/CD workflow, deployment |
| Ahmad Baihaqi | 10221063 | Lead DevOps | Makefile update, CI optimization |
| Az-Zahra Atikah Nurhaliza | 10231022 | Lead QA & Docs | Testing guide, release notes, dokumentasi |

---

## 📋 Checklist Milestone 2

- [x] Git workflow aktif (branch protection, PR, code review)
- [x] CI pipeline berjalan di GitHub Actions
- [x] Minimal 12 unit test backend passing
- [x] Minimal 7 unit test frontend passing
- [x] Badge CI status di README
- [x] Aplikasi ter-deploy ke server production
- [x] CD pipeline otomatis setelah merge ke main
- [ ] Production URL dapat diakses (update setelah dapat URL)