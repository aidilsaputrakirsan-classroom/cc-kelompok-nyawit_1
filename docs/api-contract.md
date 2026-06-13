# API Contract — SiCure

Kontrak API SiCure. Dokumen ini adalah ringkasan stabil; sumber kebenaran
interaktif tetap **Swagger UI** di `/docs` (skema OpenAPI lengkap dengan
request/response schema dan kode status).

- **Base URL (lokal):** `http://localhost:8000/api/v1`
- **Base URL (produksi):** `https://sicure-api.up.railway.app/api/v1`
- **Auth:** Bearer JWT — header `Authorization: Bearer <access_token>`
- **Format tanggal:** ISO 8601 (UTC)

---

## 1. Response Envelope

Semua endpoint mengembalikan envelope JSON yang konsisten.

Sukses (objek tunggal):
```json
{ "success": true, "data": { }, "message": "OK" }
```

Sukses (list + pagination):
```json
{
  "success": true,
  "data": [ ],
  "message": "OK",
  "pagination": { "page": 1, "per_page": 10, "total_items": 42, "total_pages": 5 }
}
```

Error:
```json
{ "success": false, "data": null, "message": "Deskripsi error" }
```
> Untuk error validasi/HTTP standar FastAPI, detail bisa berada di field `detail`.

### Observability
Setiap response menyertakan header **`X-Correlation-ID`**. Klien boleh mengirim
header `X-Correlation-ID` (atau `X-Request-ID`) sendiri; jika tidak, server
men-generate UUID. ID ini muncul di seluruh log request tersebut.

### Kode status umum
| Kode | Arti |
|------|------|
| 200 | OK |
| 201 | Resource dibuat |
| 400 | Input tidak valid |
| 401 | Token tidak ada/invalid/kedaluwarsa/di-revoke |
| 403 | Role tidak diizinkan / bukan pemilik resource |
| 404 | Resource tidak ditemukan |
| 409 | Konflik state (mis. transisi status tidak valid) |
| 413 | Body melebihi batas (produksi) |
| 422 | Validasi schema gagal |

---

## 2. Authentication

| Method | Endpoint | Auth | Body | Sukses |
|--------|----------|------|------|--------|
| POST | `/auth/register` | Admin | `{email, password, full_name, role}` | 201 user |
| POST | `/auth/register-requester` | Public | `{email, password(min 8), full_name}` | 201 user |
| POST | `/auth/login` | Public | `{email, password}` | 200 token |
| POST | `/auth/refresh` | Public | `{refresh_token}` | 200 token (rotation) |
| POST | `/auth/logout` | Auth | — | 200 (revoke access token) |
| GET | `/auth/me` | Auth | — | 200 user |

Token response:
```json
{ "access_token": "…", "refresh_token": "…", "token_type": "bearer" }
```

User response:
```json
{ "id": 1, "email": "a@b.com", "full_name": "Nama", "role": "requester", "created_at": "2026-01-01T00:00:00Z" }
```

---

## 3. Requisitions (Requester)

| Method | Endpoint | Auth | Catatan |
|--------|----------|------|---------|
| POST | `/requisitions/` | Auth | **multipart/form-data** |
| GET | `/requisitions/` | Auth | query: `page`, `per_page`, `status`, `category` |
| GET | `/requisitions/{id}` | Auth | hanya milik sendiri |
| PUT | `/requisitions/{id}` | Auth | hanya status `SUBMITTED`/`REJECTED` |
| DELETE | `/requisitions/{id}` | Auth | hanya status `SUBMITTED`/`REJECTED` |
| GET | `/requisitions/categories` | Auth | kategori unik dari nama item |

Body create (multipart):
- `title` (str), `justification` (str, opsional)
- `items_json` — JSON array: `[{item_name, quantity, unit_of_measure, estimated_unit_price}]`
- `vendor_quotes_json` — JSON array: `[{vendor_name, vendor_contact, quoted_price, survey_date, is_recommended}]`
- `vendor_quotes[i].survey_evidence` — file bukti survei per vendor (JPG/PNG/PDF, ≤5MB)

Aturan vendor: total PR ≤ ambang (`QUOTE_THRESHOLD`, default Rp5.000.000) → minimal
1 vendor; di atas ambang → minimal 3 vendor; tepat 1 vendor `is_recommended`.

---

## 4. Requisitions (Admin)

| Method | Endpoint | Auth | Catatan |
|--------|----------|------|---------|
| GET | `/requisitions/admin/` | Admin | semua PR (pagination + filter) |
| GET | `/requisitions/admin/{id}` | Admin | detail PR mana pun |
| PUT | `/requisitions/admin/{id}/review` | Admin | `{action: "APPROVE"\|"REJECT", approval_note}` |

`APPROVE` otomatis menerbitkan PO dan men-set status `PO_ISSUED`. `REJECT` → `REJECTED`.

---

## 5. Purchase Orders

| Method | Endpoint | Auth | Catatan |
|--------|----------|------|---------|
| GET | `/purchase-orders/` | Admin | list semua PO |
| GET | `/purchase-orders/{po_id}` | Admin | detail PO |
| GET | `/purchase-orders/by-pr/{pr_id}` | Admin | PO berdasarkan PR |
| GET | `/purchase-orders/{pr_id}/my-po` | Auth | PO untuk PR milik sendiri |
| POST | `/purchase-orders/{pr_id}/issue` | Admin | legacy — hanya PR `APPROVED` |

---

## 6. GRN (Goods Receipt Note)

| Method | Endpoint | Auth | Catatan |
|--------|----------|------|---------|
| POST | `/grn/{po_id}/submit-doc` | Auth | **multipart**: `commercial_invoice`, `goods_photo` |
| GET | `/grn/{grn_id}` | Auth | detail GRN |
| GET | `/grn/by-po/{po_id}` | Auth | GRN berdasarkan PO |
| PUT | `/grn/admin/{grn_id}/verify` | Admin | `{status: "VERIFIED"\|"CLOSED", verification_note}` |
| PUT | `/grn/admin/{grn_id}/return` | Admin | `{verification_note}` → kembali ke `PO_ISSUED` |

Transisi verify: `DOC_SUBMITTED → VERIFIED → CLOSED` (berurutan; target status harus sesuai).

---

## 7. Health

| Method | Endpoint | Auth | Sukses |
|--------|----------|------|--------|
| GET | `/health` | Public | `{status, service, version, database}` |
| GET | `/api/v1/health` | Public | envelope + `components.database` |

`200` jika sehat, `503` jika database tidak terhubung.
