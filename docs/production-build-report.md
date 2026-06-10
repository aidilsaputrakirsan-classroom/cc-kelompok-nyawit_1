# Production Build Report — Frontend

**Branch:** `feature/production-build`  
**Tanggal:** 2026-06-10  
**Perintah:** `npm run build:size` (dari folder `frontend/`)

## Konfigurasi

| File | Keterangan |
|------|------------|
| `frontend/.env.production` | `VITE_API_BASE_URL` → backend Railway (`/api/v1`) |
| `frontend/Dockerfile` | `ARG VITE_API_BASE_URL` untuk build Docker production |

## Ukuran Build (`dist/`)

| Metrik | Nilai |
|--------|-------|
| **Total** | **389.0 KB** |
| Gzip terbesar (vendor-react) | 73.85 KB |
| CSS utama | 6.17 KB (gzip) |

### File terbesar

| Ukuran | File |
|--------|------|
| 225.8 KB | `assets/vendor-react-*.js` |
| 35.6 KB | `assets/vendor-utils-*.js` |
| 34.2 KB | `assets/index-*.css` |
| 14.6 KB | `assets/PRDetail-*.js` (admin) |

## Error Handling Production

- `ErrorBoundary` — pesan ramah, detail error disembunyikan di production
- `ApiErrorNotifier` — toast otomatis untuk error server (5xx) & jaringan
- `ApiErrorFallback` — komponen inline untuk halaman yang gagal memuat data
- `getFriendlyApiErrorMessage()` — mapper pesan error API

## Verifikasi

```bash
cd frontend
npm run build:size
```

Build harus selesai tanpa error TypeScript.
