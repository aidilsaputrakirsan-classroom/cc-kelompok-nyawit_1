# Production Test — SiCure (Modul 11)

Dokumentasi smoke test setelah deploy ke Railway.

**Tim:** Kelompok Nyawit  
**Tanggal uji:** _(isi setelah deploy)_  
**Environment:** Production (Railway)

---

## URL Production

| Service | URL |
|---------|-----|
| Frontend | _(isi URL Railway frontend)_ |
| Backend API | _(isi URL Railway backend)_ |
| API Docs | _(backend-url)/docs |
| Health | _(backend-url)/health |

---

## Smoke Test Checklist

| # | Langkah | Development (localhost) | Production (Railway) | Status |
|---|---------|------------------------|---------------------|--------|
| 1 | Halaman frontend load tanpa error | ☐ | ☐ | |
| 2 | Backend `/health` → `healthy`, database `connected` | ☐ | ☐ | |
| 3 | Login admin (`admin@sicure.com` / `admin1234`) | ☐ | ☐ | |
| 4 | Login requester (`requester1@sicure.com` / `requester1234`) | ☐ | ☐ | |
| 5 | Requester: buat Purchase Requisition baru | ☐ | ☐ | |
| 6 | Requester: lihat daftar PR di dashboard | ☐ | ☐ | |
| 7 | Admin: lihat & approve/reject PR | ☐ | ☐ | |
| 8 | Admin: buat PO dari PR yang disetujui | ☐ | ☐ | |

---

## Hasil Health Check

```bash
curl -s https://YOUR-BACKEND-URL/health | jq
```

**Response production:**

```json

```

---

## Catatan Issue

| Issue | Gejala | Solusi yang diterapkan |
|-------|--------|------------------------|
| | | |

---

## Kesimpulan

- [ ] Semua smoke test **PASS** di production
- [ ] CD pipeline deploy otomatis setelah merge ke `main`
- [ ] README sudah berisi link live demo

---

*Diisi oleh Lead QA & Docs setelah Workshop 11.4.*
