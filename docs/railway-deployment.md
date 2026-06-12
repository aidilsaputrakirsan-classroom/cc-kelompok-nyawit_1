# Railway Deployment Guide — SiCure (Monolith)

Panduan deploy aplikasi **monolith** SiCure (backend FastAPI + frontend React + PostgreSQL) ke [Railway](https://railway.app). Menggantikan deploy via DeployCC sebelumnya, sehingga tim punya kontrol penuh atas deployment.

> Arsitektur deploy: **1 backend service + 1 frontend service + 1 PostgreSQL**, semua dalam satu Railway project. Deploy otomatis via integrasi GitHub Railway (push ke `main` → auto-deploy). Tidak memakai GitHub Actions untuk deploy; `ci.yml` tetap dipakai hanya untuk test.

---

## 0. Prasyarat

- Akun Railway (login via GitHub di https://railway.app).
- **Verifikasi akun** (connect GitHub) agar mendapat **Full Trial** — tanpa verifikasi, outbound network dibatasi (Limited Trial) dan deploy bisa bermasalah.
- Repo ini sudah ter-push ke GitHub.

---

## 1. Buat Project + PostgreSQL

1. Railway Dashboard → **New Project** → **Empty Project**. Beri nama `sicure`.
2. **+ Create** → **Database** → **Add PostgreSQL**. Railway membuat service `Postgres` lengkap dengan variabel `DATABASE_URL`.

---

## 2. Deploy Backend

1. **+ Create** → **GitHub Repo** → pilih repo ini.
2. Buka service yang terbuat → **Settings**:
   - **Root Directory:** `/` (biarkan root repo — Dockerfile backend memakai konteks root)
   - **Build → Dockerfile Path:** `backend/Dockerfile`
   - Beri nama service: `backend`
3. **Variables** → tambahkan:

| Variable | Value | Catatan |
|----------|-------|---------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Referensi ke service Postgres. App otomatis mengubah `postgresql://` → `postgresql+asyncpg://`. |
| `JWT_SECRET` | (random) | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_REFRESH_SECRET` | (random lain) | generate terpisah |
| `APP_ENV` | `production` | mengaktifkan mode produksi (CORS ketat, limit body) |
| `ALLOWED_ORIGINS` | `https://<frontend-domain>` | isi setelah domain frontend ada (langkah 3) |
| `SEED_ON_STARTUP` | `true` | **hanya untuk deploy pertama** untuk membuat user demo, lalu set `false` |

4. **Settings → Networking → Generate Domain.** Catat domain backend, mis. `https://backend-xxxx.up.railway.app`.
5. Tunggu deploy. Container otomatis menjalankan `alembic upgrade head` lalu uvicorn pada `$PORT`.
6. Verifikasi: buka `https://backend-xxxx.up.railway.app/health` → harus `{"status":"healthy","database":"connected"}`.

> Setelah deploy pertama sukses & user ter-seed, ubah `SEED_ON_STARTUP` menjadi `false` agar tidak men-seed ulang setiap restart.

---

## 3. Deploy Frontend

1. **+ Create** → **GitHub Repo** → pilih repo yang sama.
2. **Settings**:
   - **Root Directory:** `/`
   - **Build → Dockerfile Path:** `frontend/Dockerfile`
   - Nama service: `frontend`
3. **Variables** → tambahkan (di-bake saat build oleh Vite):

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | `https://backend-xxxx.up.railway.app/api/v1` |

4. **Settings → Networking → Generate Domain.** Catat domain frontend.
   - Jika Railway menanyakan target port, pakai **80** (atau biarkan auto — nginx listen pada `$PORT` yang di-inject Railway).
5. Setelah domain frontend ada, kembali ke service **backend** → update `ALLOWED_ORIGINS` ke domain frontend (mis. `https://frontend-yyyy.up.railway.app`) → backend auto-redeploy.

> Catatan: `VITE_API_BASE_URL` di-compile ke dalam bundle saat build. Jika diubah, frontend perlu **redeploy** (bukan sekadar restart).

---

## 4. CD — Auto Deploy

Railway otomatis memantau repo GitHub. Setiap **push/merge ke `main`**, kedua service (backend & frontend) akan rebuild & redeploy sendiri. Tidak perlu workflow deploy di GitHub Actions.

`ci.yml` tetap berjalan untuk test (pytest + vitest + build Docker) pada setiap push/PR ke `main`.

Opsional: di Railway service Settings → **Build**, batasi auto-deploy hanya pada perubahan path tertentu (watch paths) — mis. backend hanya redeploy jika `backend/**` berubah.

---

## 5. Smoke Test Produksi

1. Buka domain frontend → halaman login muncul.
2. Login `admin@sicure.com` / `admin1234` (jika sudah di-seed).
3. Buat PR → approve → terbitkan PO → upload GRN → verify.
4. `GET https://backend-xxxx.up.railway.app/health` → `healthy`.
5. Swagger: `https://backend-xxxx.up.railway.app/docs`.

---

## 6. Variabel Lingkungan (Ringkasan)

### Backend
| Variable | Wajib | Default |
|----------|-------|---------|
| `DATABASE_URL` | ✅ | — (`${{Postgres.DATABASE_URL}}`) |
| `JWT_SECRET` | ✅ | `change-me` (ganti!) |
| `JWT_REFRESH_SECRET` | ✅ | `change-me-refresh` (ganti!) |
| `APP_ENV` | disarankan | `development` |
| `ALLOWED_ORIGINS` | ✅ (produksi) | `http://localhost:5173` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | opsional | `30` |
| `MAX_UPLOAD_SIZE_MB` | opsional | `5` |
| `SEED_ON_STARTUP` | opsional | `false` |
| `PORT` | otomatis | di-inject Railway |

### Frontend
| Variable | Wajib | Catatan |
|----------|-------|---------|
| `VITE_API_BASE_URL` | ✅ | URL backend + `/api/v1`, di-bake saat build |
| `PORT` | otomatis | di-inject Railway |

---

## 7. Troubleshooting

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| Backend `Application failed to respond` | App tidak listen di `$PORT` | Sudah ditangani (uvicorn pakai `${PORT:-8000}`). Pastikan tidak meng-override `PORT` manual. |
| `502/healthcheck failed` | Migrasi gagal / DB belum siap | Cek Deploy Logs; pastikan `DATABASE_URL` benar (`${{Postgres.DATABASE_URL}}`). |
| CORS error di browser | `ALLOWED_ORIGINS` tidak sama dengan domain frontend | Set `ALLOWED_ORIGINS` ke domain frontend persis (tanpa trailing slash). |
| Frontend memanggil `localhost:8000` | `VITE_API_BASE_URL` tidak di-set saat build | Set variable lalu **redeploy** frontend. |
| Outbound/network terbatas | Akun belum terverifikasi (Limited Trial) | Verifikasi akun di railway.com/verify. |

---

## Catatan Biaya (Trial)

- Trial: hibah **$5 sekali pakai**, berlaku **30 hari**, maks **1 GB RAM** & **5 service per project**.
- Estimasi monolith (backend + 1 Postgres) jika nyala 24/7 ≈ **$6–7/bulan**, jadi $5 cukup untuk ~3 minggu nonstop. Debug di lokal dulu untuk menghemat; nyalakan serius menjelang demo.
- Deploy ulang/trial-error **tidak** dikenai biaya per percobaan — yang dihitung adalah waktu container berjalan.
