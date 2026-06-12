# API Contract — SiCure Microservices

## Base URLs

| Environment       | Gateway URL                     |
| ----------------- | ------------------------------- |
| Local Development | http://localhost                |
| Production        | https://your-app.up.railway.app |

---

## Authentication

Semua endpoint yang dilindungi memerlukan JWT Token.

Header:

```http
Authorization: Bearer <access_token>
```

---

## Error Response Format

```json
{
  "detail": "Error message"
}
```

| Status Code | Keterangan          |
| ----------- | ------------------- |
| 200         | Success             |
| 201         | Created             |
| 400         | Bad Request         |
| 401         | Unauthorized        |
| 403         | Forbidden           |
| 404         | Not Found           |
| 409         | Conflict            |
| 422         | Validation Error    |
| 429         | Too Many Requests   |
| 503         | Service Unavailable |

---

# Auth Service

## GET /health

Deskripsi: Health Check Auth Service.

---

## POST /register

Deskripsi: Registrasi pengguna baru oleh Admin.

---

## POST /register-requester

Deskripsi: Registrasi requester secara mandiri.

---

## POST /login

Deskripsi: Login pengguna dan menghasilkan JWT Access Token.

Request:

```json
{
  "email": "user@example.com",
  "password": "Password123"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token"
}
```

---

## POST /refresh

Deskripsi: Memperbarui Access Token menggunakan Refresh Token.

---

## POST /logout

Deskripsi: Logout pengguna dan melakukan revoke token.

---

## GET /me

Deskripsi: Menampilkan informasi user yang sedang login.

---

## GET /verify

Deskripsi: Verifikasi JWT Token antar service.

---

## GET /metrics

Deskripsi: Monitoring metrics Auth Service.

---

# Procurement Service

## GET /health

Deskripsi: Aggregated Health Check Service.

---

## GET /api/v1/health

Deskripsi: API Health Check Procurement Service.

---

# Purchase Requisition API

Base Path:

```text
/api/v1/requisitions
```

## POST /api/v1/requisitions

Deskripsi: Membuat Purchase Requisition baru.

---

## GET /api/v1/requisitions

Deskripsi: Menampilkan daftar Purchase Requisition milik requester.

Query Parameters:

| Parameter | Type    | Description             |
| --------- | ------- | ----------------------- |
| page      | integer | Nomor halaman           |
| per_page  | integer | Jumlah data per halaman |
| status    | string  | Filter status           |
| category  | string  | Filter kategori         |

---

## GET /api/v1/requisitions/{pr_id}

Deskripsi: Menampilkan detail Purchase Requisition berdasarkan ID.

---

## GET /api/v1/requisitions/categories

Deskripsi: Menampilkan daftar kategori item.

---

## PUT /api/v1/requisitions/{pr_id}

Deskripsi: Mengubah Purchase Requisition yang masih berstatus SUBMITTED.

---

## DELETE /api/v1/requisitions/{pr_id}

Deskripsi: Menghapus Purchase Requisition yang masih berstatus SUBMITTED.

---

# Purchase Requisition Admin API

Base Path:

```text
/api/v1/requisitions/admin
```

## GET /api/v1/requisitions/admin

Deskripsi: Menampilkan seluruh Purchase Requisition.

Query Parameters:

| Parameter    | Type    | Description             |
| ------------ | ------- | ----------------------- |
| page         | integer | Nomor halaman           |
| per_page     | integer | Jumlah data per halaman |
| status       | string  | Filter status PR        |
| requester_id | integer | Filter requester        |
| category     | string  | Filter kategori item    |

---

## PUT /api/v1/requisitions/admin/{pr_id}/review

Deskripsi: Approve atau Reject Purchase Requisition.

---

## GET /api/v1/requisitions/admin/categories

Deskripsi: Menampilkan seluruh kategori item pada sistem.

---

# Purchase Order API

Base Path:

```text
/api/v1/purchase-orders
```

## POST /api/v1/purchase-orders/{pr_id}/issue

Role: Admin

Deskripsi: Menerbitkan Purchase Order dari Purchase Requisition yang sudah APPROVED.

---

## GET /api/v1/purchase-orders/{pr_id}/my-po

Role: Requester

Deskripsi: Menampilkan Purchase Order untuk PR milik requester.

---

## GET /api/v1/purchase-orders

Role: Admin

Deskripsi: Menampilkan seluruh Purchase Order.

Query Parameters:

| Parameter | Type    | Description             |
| --------- | ------- | ----------------------- |
| page      | integer | Nomor halaman           |
| per_page  | integer | Jumlah data per halaman |

---

# Goods Receipt Note (GRN) API

Base Path:

```text
/api/v1/grn
```

## POST /api/v1/grn/{po_id}/submit-doc

Deskripsi: Upload dokumen Goods Receipt Note.

File Upload:

| Field              | Type        | Description          |
| ------------------ | ----------- | -------------------- |
| commercial_invoice | JPG/PNG/PDF | Faktur komersial     |
| goods_photo        | JPG/PNG/PDF | Foto barang diterima |

Ketentuan:

* Maksimal 5 MB per file
* Hanya JPG, PNG, dan PDF
* Hanya requester pemilik PO yang dapat mengunggah

---

## GET /api/v1/grn/{grn_id}

Deskripsi: Menampilkan detail dokumen GRN.

---

# GRN Admin API

Base Path:

```text
/api/v1/grn/admin
```

## PUT /api/v1/grn/admin/{grn_id}/verify

Role: Admin

Deskripsi: Verifikasi dokumen GRN.

Status Workflow:

```text
DOC_SUBMITTED → VERIFIED → CLOSED
```

Admin wajib memberikan verification note saat proses verifikasi.

---

# Procurement Workflow

```text
Requester
    ↓
Create Purchase Requisition
    ↓
SUBMITTED
    ↓
Admin Review
    ↓
APPROVED / REJECTED
    ↓
Purchase Order Issued
    ↓
PO_ISSUED
    ↓
Requester Upload GRN
    ↓
DOC_SUBMITTED
    ↓
Admin Verification
    ↓
VERIFIED
    ↓
CLOSED
```
