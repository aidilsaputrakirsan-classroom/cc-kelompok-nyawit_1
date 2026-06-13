# Release Notes — SiCure

Riwayat rilis SiCure (Sistem Informasi Procurement). Versi mengikuti
[Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

---

## v3.0.0 — Final Release (UAS)

Rilis final: konsolidasi ke arsitektur **monolith** di Railway, observability,
dan CI/CD lengkap dengan integration test.

**Highlights**
- **Deployment**: pindah dari DeployCC ke **Railway**; fokus monolith
  (backend + frontend + PostgreSQL) dengan auto-deploy dari `main`.
- **Observability (Minggu 14)**: structured logging format **JSON**, **correlation
  ID** per request (header `X-Correlation-ID`), health check `/health` & `/api/v1/health`.
- **CI/CD (Minggu 10–11)**: pipeline `test (unit + integration) → build → verify-deploy`;
  health check production URL setelah deploy.
- **Procurement lengkap**: PR + perbandingan penawaran vendor (3-quotation),
  approval + penerbitan PO, GRN, verifikasi & penutupan.
- **Keamanan (Minggu 15)**: CORS ketat di produksi, batas ukuran body, validasi
  upload, JWT + bcrypt, token revocation/blacklist, secrets via environment variables.
- **Dokumentasi**: README final, API contract, deployment guide, diagram arsitektur,
  reflection paper per anggota.

**Catatan teknis**
- Migrasi `alembic upgrade head` berjalan otomatis saat startup container.
- Test: pytest (unit + integration, coverage ≥40%) + Vitest frontend.

---

## v2.0.0 — Cloud, CI/CD & Eksperimen Microservices (Minggu 9–13)

Iterasi menuju cloud-native dan eksplorasi pemecahan layanan.

- **Git workflow & code review (Minggu 9)**: branching strategy, PR template,
  CODEOWNERS, branch protection.
- **Continuous Integration (Minggu 10)**: GitHub Actions — automated test backend
  (pytest) & frontend (Vitest), build Docker image.
- **Continuous Delivery/Deployment (Minggu 11)**: pipeline deploy ke cloud,
  manajemen secrets & environment variables.
- **Microservices (Minggu 12)**: eksperimen dekomposisi monolith menjadi
  Auth Service + Procurement Service, API Gateway (Nginx), Docker Compose multi-service.
- **Reliability & resilience (Minggu 13)**: retry logic, timeout, circuit breaker,
  graceful degradation, integration test antar service.

> Catatan: arsitektur microservices kemudian **di-konsolidasi kembali ke monolith**
> pada v3.0.0 untuk menyederhanakan deployment dan biaya di Railway. Pembelajaran
> dari fase ini didokumentasikan di reflection paper.

---

## v1.0.0 — MVP Procurement Monolith (Minggu 1–8)

Fondasi aplikasi full-stack.

- **Backend (FastAPI)**: health check, endpoint awal, struktur modular
  (routers, models, schemas, services).
- **Auth**: JWT (access + refresh), registrasi requester, RBAC Admin/Requester.
- **CRUD Procurement**: Purchase Requisition + line items, fitur search/filter
  & pagination, kategori.
- **Frontend (React + TypeScript + Vite)**: UI login/register, arsitektur komponen
  modular, integrasi API.
- **Containerization**: Dockerfile backend & frontend (multi-stage frontend),
  Docker Compose, healthcheck, non-root user (frontend), seed idempotent.

---

## Konvensi Versi

| Bagian | Naik jika |
|--------|-----------|
| MAJOR | perubahan arsitektur/kontrak API yang breaking |
| MINOR | fitur baru yang backward-compatible |
| PATCH | perbaikan bug / dokumentasi |

Rilis final ditandai dengan git tag `v3.0.0`:
```bash
git tag -a v3.0.0 -m "Final release UAS"
git push origin v3.0.0
```
