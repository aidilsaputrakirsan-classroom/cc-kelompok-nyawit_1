# Deployment Guide — SiCure (Modul 11)

Panduan deploy full-stack SiCure ke **Railway** dengan Continuous Delivery via GitHub Actions.

---

## Prasyarat

- Akun [Railway](https://railway.app/) (login via GitHub)
- Repository tim terhubung ke GitHub
- CI pipeline Modul 10/11 berjalan di branch `main`

---

## 1. Setup Railway Project

1. Buka https://railway.app/dashboard
2. **New Project** → **Empty Project**
3. Beri nama: `sicure-team-XX` (ganti XX dengan nomor tim)

### Tambah PostgreSQL

1. **+ Add Service** → **Database** → **Add PostgreSQL**
2. Buka service PostgreSQL → tab **Variables**
3. Catat `DATABASE_URL` (format: `postgresql://postgres:...@...railway.internal:5432/railway`)

---

## 2. Deploy Backend

1. **+ Add Service** → **GitHub Repo** → pilih repository tim
2. Konfigurasi:
   - **Service name:** `backend`
   - **Root Directory:** `/backend`
   - **Builder:** Dockerfile

3. **Settings** → **Networking** → **Generate Domain**
4. Catat URL, misal: `https://sicure-backend-xxx.up.railway.app`

### Environment Variables (Backend)

| Variable | Value | Catatan |
|----------|-------|---------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Reference ke service PostgreSQL |
| `JWT_SECRET` | (random 64 char) | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `CORS_ORIGINS` | `https://sicure-frontend-xxx.up.railway.app` | URL frontend production |
| `ENVIRONMENT` | `production` | Mengaktifkan mode production |
| `SEED_ON_STARTUP` | `true` | Hanya untuk setup pertama |

> Aplikasi juga menerima alias: `SECRET_KEY` → `JWT_SECRET`, `ALLOWED_ORIGINS` → `CORS_ORIGINS`.

### Verifikasi Backend

```bash
curl https://sicure-backend-xxx.up.railway.app/health
```

Response yang diharapkan:

```json
{
  "status": "healthy",
  "service": "backend",
  "version": "1.0.0",
  "database": "connected",
  "env": "production"
}
```

---

## 3. Deploy Frontend

1. **+ Add Service** → **GitHub Repo** (repository sama)
2. Konfigurasi:
   - **Service name:** `frontend`
   - **Root Directory:** `/frontend`
   - **Builder:** Dockerfile

3. **Generate Domain** → catat URL frontend

### Update API URL Production

Edit `frontend/.env.production`:

```env
VITE_API_BASE_URL=https://sicure-backend-xxx.up.railway.app/api/v1
```

Push perubahan → Railway auto-redeploy frontend.

### Update CORS Backend

Setelah frontend punya URL, update `CORS_ORIGINS` di service backend dengan URL frontend production.

---

## 4. GitHub Secrets (CD Pipeline)

Repository → **Settings** → **Secrets and variables** → **Actions**:

| Secret | Keterangan |
|--------|------------|
| `RAILWAY_TOKEN` | Token dari https://railway.app/account/tokens |
| `RAILWAY_BACKEND_URL` | URL backend production (untuk health check CD) |
| `RAILWAY_FRONTEND_URL` | URL frontend production (untuk deployment summary) |

### Link Project Railway (sekali)

Di laptop tim, jalankan:

```bash
npm install -g @railway/cli
railway login
cd backend && railway link
cd ../frontend && railway link
```

Pastikan nama service di Railway: `backend` dan `frontend` (sesuai workflow).

---

## 5. Alur CI/CD

```mermaid
flowchart LR
    PR[Pull Request] --> CI[CI: test + build]
    MERGE[Merge ke main] --> CI
    CI --> CD[CD: deploy Railway]
    CD --> PROD[Production URL]
```

- **PR / push branch lain:** hanya CI (test + build Docker)
- **Push ke `main`:** CI + CD (deploy otomatis)

---

## 6. Troubleshooting

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| `Application failed to start` | Dockerfile / dependency error | Cek **Deploy Logs** di Railway |
| `database: disconnected` di `/health` | `DATABASE_URL` salah | Gunakan `${{Postgres.DATABASE_URL}}` |
| CORS error di browser | `CORS_ORIGINS` tidak sesuai | Update dengan URL frontend Railway |
| Frontend blank / API error | `VITE_API_BASE_URL` masih localhost | Update `.env.production`, rebuild |
| CD gagal `railway up` | Project belum di-link | Jalankan `railway link` di folder service |
| Login gagal setelah redeploy | `JWT_SECRET` berubah | Pastikan secret konsisten di Railway |

### Rollback Manual

1. Railway Dashboard → service → **Deployments**
2. Pilih deployment sebelumnya → **Redeploy**

---

## 7. Deploy Lokal (Docker Compose)

Untuk development:

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

*Modul 11 — Continuous Deployment, Komputasi Awan ITK.*
