# Release Notes — Milestone 2

## Versi: 2.0.0
**Tanggal Rilis:** [Isi tanggal saat merge]
**Tag:** v2.0
**Repository:** [Link repository GitHub tim]

---

## 🌐 URL Production

| Layanan | URL |
|---------|-----|
| Frontend | *Coming Soon — akan diisi setelah deploy ke Railway* |
| Backend API | *Coming Soon — akan diisi setelah deploy ke Railway* |
| API Docs (Swagger) | *Coming Soon* |

---

## 🆕 Fitur Baru (Milestone 2)

### CI/CD Pipeline (GitHub Actions)
- Workflow otomatis berjalan setiap ada push atau Pull Request ke branch `main`
- Job `test-backend`: menjalankan pytest secara otomatis
- Job `test-frontend`: menjalankan Vitest secara otomatis
- Job `build-docker`: membangun Docker image backend dan frontend
- Badge CI status ditampilkan di README

### Automated Testing — Backend (pytest)
- Konfigurasi pytest dengan SQLite in-memory (tidak bergantung PostgreSQL saat testing)
- Test autentikasi: register, login, duplikat email, password salah
- Test CRUD item: create, read, update, delete, search
- Test health endpoint
- Coverage testing tersedia via `pytest --cov`

### Automated Testing — Frontend (Vitest)
- Setup Vitest dengan jsdom dan Testing Library
- Test komponen Header
- Test komponen ItemCard (render, edit, delete)
- Test API service (fetch, error handling)

### Branch Protection & Git Workflow
- Branch `main` dilindungi — tidak bisa push langsung
- Setiap perubahan wajib melalui Pull Request dan code review
- Squash and merge diterapkan untuk menjaga history tetap bersih
- File `CODEOWNERS` mengatur reviewer otomatis per area kode
- PR template tersedia untuk standardisasi

### Deployment ke Railway (Continuous Deployment)
- Backend ter-deploy ke Railway dengan PostgreSQL managed
- Frontend ter-deploy ke Railway
- CD pipeline otomatis berjalan setelah merge ke `main`
- Environment variables dikelola via Railway dashboard dan GitHub Secrets

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
| Database | PostgreSQL | 16 |
| Container | Docker + Docker Compose | — |
| Testing Backend | pytest + pytest-asyncio + httpx | ≥ 8.0.0 |
| Testing Frontend | Vitest + Testing Library | — |
| CI/CD | GitHub Actions | — |
| Cloud Deployment | Railway (PaaS) | — |

---

## 📊 Statistik Milestone 2

| Metrik | Jumlah |
|--------|--------|
| Unit test backend | ≥ 12 test |
| Unit test frontend | ≥ 7 test |
| CI pipeline jobs | 4 jobs (test-backend, test-frontend, build-docker, deploy) |
| PR yang di-merge | [Isi jumlah PR] |
| Total commit | [Isi jumlah commit] |

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

- Tidak ada known issues saat ini

---

## 👥 Kontribusi Tim

| Nama | NIM | Peran | Kontribusi Utama |
|------|-----|-------|-----------------|
| Muchlis Wahyu Saputra | 10231054 | Lead Backend | pytest, unit test backend, health endpoint |
| Ranaya Chintya Mahitsa | 10231078 | Lead Frontend | Vitest, unit test frontend, dark mode |
| Andi Adam Firdaus | 10211014 | Lead DevOps | GitHub Actions CI/CD workflow, Railway deploy |
| Ahmad Baihaqi | 10221063 | Lead DevOps | Makefile update, CI optimization |
| Az-Zahra Atikah Nurhaliza | 10231022 | Lead QA & Docs | Testing guide, release notes, dokumentasi |

---

## 📋 Checklist Milestone 2

- [x] Git workflow aktif (branch protection, PR, code review)
- [x] CI pipeline berjalan di GitHub Actions
- [x] Minimal 12 unit test backend passing
- [x] Minimal 7 unit test frontend passing
- [x] Badge CI status di README
- [x] Aplikasi ter-deploy ke Railway
- [x] CD pipeline otomatis setelah merge ke main
- [ ] Production URL dapat diakses (update setelah deploy)