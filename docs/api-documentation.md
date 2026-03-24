# 📋 API Documentation — SICURE Cloud App

Dokumentasi lengkap seluruh endpoint REST API untuk sistem **SICURE (Sistem Information Procurement)**.

**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)

---

## 🔐 Autentikasi

Sebagian besar endpoint memerlukan JWT token.  
Sertakan token di setiap request dengan header:

```
Authorization: Bearer <access_token>
```

Token diperoleh dari endpoint `POST /auth/login`.

---

## 📌 Daftar Endpoint

| # | Method | Endpoint | Auth Required | Deskripsi |
|---|--------|----------|:-------------:|-----------|
| 1 | `GET` | `/health` | ❌ | Health check server |
| 2 | `POST` | `/auth/register` | ❌ | Registrasi user baru |
| 3 | `POST` | `/auth/login` | ❌ | Login, dapatkan JWT token |
| 4 | `GET` | `/auth/me` | ✅ | Profil user saat ini |
| 5 | `GET` | `/items` | ✅ | Daftar items dengan pagination & search |
| 6 | `POST` | `/items` | ✅ | Buat item baru |
| 7 | `GET` | `/items/{id}` | ✅ | Detail satu item |
| 8 | `PUT` | `/items/{id}` | ✅ | Update item |
| 9 | `DELETE` | `/items/{id}` | ✅ | Hapus item |
| 10 | `GET` | `/items/stats` | ✅ | Statistik inventory |
| 11 | `GET` | `/team` | ❌ | Info tim |

---

## 1. Health Check

```
GET /health
```

**Auth:** Tidak diperlukan

**Response 200:**
```json
{
  "status": "healthy",
  "version": "0.5.0"
}
```

**curl:**
```bash
curl http://localhost:8000/health
```

---

## 2. Register User Baru

```
POST /auth/register
```

**Auth:** Tidak diperlukan

**Request Body:**
```json
{
  "email": "user@student.itk.ac.id",
  "name": "Nama Lengkap",
  "password": "Passw0rd!"
}
```

**Validasi:**
- `email`: format email valid, unik
- `name`: 2–100 karakter
- `password`: min 8 karakter, harus ada huruf besar, angka, dan karakter khusus (`@$!%*?&`)

**Response 201:**
```json
{
  "id": 1,
  "email": "user@student.itk.ac.id",
  "name": "Nama Lengkap",
  "is_active": true,
  "created_at": "2026-03-25T00:00:00"
}
```

**Response 400 (email sudah terdaftar):**
```json
{
  "detail": "Email sudah terdaftar. Gunakan email lain atau login."
}
```

**curl:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@student.itk.ac.id","name":"Nama Lengkap","password":"Passw0rd!"}'
```

---

## 3. Login

```
POST /auth/login
```

**Auth:** Tidak diperlukan

**Request Body:**
```json
{
  "email": "user@student.itk.ac.id",
  "password": "Passw0rd!"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@student.itk.ac.id",
    "name": "Nama Lengkap",
    "is_active": true,
    "created_at": "2026-03-25T00:00:00"
  }
}
```

**Response 401 (salah kredensial):**
```json
{
  "detail": "Email atau password salah. Periksa kembali kredensial Anda."
}
```

**curl:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@student.itk.ac.id","password":"Passw0rd!"}'
```

---

## 4. Get Current User (Me)

```
GET /auth/me
```

**Auth:** ✅ Required

**Response 200:**
```json
{
  "id": 1,
  "email": "user@student.itk.ac.id",
  "name": "Nama Lengkap",
  "is_active": true,
  "created_at": "2026-03-25T00:00:00"
}
```

**Response 401 (token tidak valid):**
```json
{
  "detail": "Token tidak valid atau sudah expired"
}
```

**curl:**
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

## 5. Get All Items

```
GET /items
```

**Auth:** ✅ Required

**Query Parameters:**

| Parameter | Tipe | Default | Keterangan |
|-----------|------|---------|-----------|
| `skip` | int | 0 | Jumlah item yang dilewati (pagination) |
| `limit` | int | 20 | Jumlah item per halaman (max: 100) |
| `search` | string | null | Cari berdasarkan nama/deskripsi |

**Contoh Request:**
```
GET /items?skip=0&limit=20&search=laptop
```

**Response 200:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Laptop",
      "description": "Laptop untuk cloud computing",
      "price": 15000000.0,
      "quantity": 5,
      "created_at": "2026-03-25T00:00:00",
      "updated_at": null
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

**curl:**
```bash
curl "http://localhost:8000/items?skip=0&limit=20" \
  -H "Authorization: Bearer <access_token>"
```

---

## 6. Create Item

```
POST /items
```

**Auth:** ✅ Required

**Request Body:**
```json
{
  "name": "Laptop",
  "description": "Laptop untuk cloud computing",
  "price": 15000000,
  "quantity": 5
}
```

**Validasi:**
- `name`: 1–100 karakter, wajib diisi
- `description`: opsional, max 500 karakter
- `price`: harus > 0
- `quantity`: harus >= 0

**Response 201:**
```json
{
  "id": 1,
  "name": "Laptop",
  "description": "Laptop untuk cloud computing",
  "price": 15000000.0,
  "quantity": 5,
  "created_at": "2026-03-25T00:00:00",
  "updated_at": null
}
```

**curl:**
```bash
curl -X POST http://localhost:8000/items \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop","description":"Laptop cloud","price":15000000,"quantity":5}'
```

---

## 7. Get Item by ID

```
GET /items/{item_id}
```

**Auth:** ✅ Required

**Path Parameter:** `item_id` (integer)

**Response 200:**
```json
{
  "id": 1,
  "name": "Laptop",
  "description": "Laptop untuk cloud computing",
  "price": 15000000.0,
  "quantity": 5,
  "created_at": "2026-03-25T00:00:00",
  "updated_at": null
}
```

**Response 404:**
```json
{
  "detail": "Item dengan ID 99 tidak ditemukan."
}
```

**curl:**
```bash
curl http://localhost:8000/items/1 \
  -H "Authorization: Bearer <access_token>"
```

---

## 8. Update Item

```
PUT /items/{item_id}
```

**Auth:** ✅ Required

**Path Parameter:** `item_id` (integer)

**Request Body** (semua field opsional — partial update):
```json
{
  "price": 14000000,
  "quantity": 3
}
```

**Response 200:**
```json
{
  "id": 1,
  "name": "Laptop",
  "description": "Laptop untuk cloud computing",
  "price": 14000000.0,
  "quantity": 3,
  "created_at": "2026-03-25T00:00:00",
  "updated_at": "2026-03-25T01:00:00"
}
```

**Response 404:**
```json
{
  "detail": "Item dengan ID 99 tidak ditemukan atau tidak dapat diupdate."
}
```

**curl:**
```bash
curl -X PUT http://localhost:8000/items/1 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"price":14000000}'
```

---

## 9. Delete Item

```
DELETE /items/{item_id}
```

**Auth:** ✅ Required

**Path Parameter:** `item_id` (integer)

**Response 204:** No Content (item berhasil dihapus)

**Response 404:**
```json
{
  "detail": "Item dengan ID 99 tidak ditemukan."
}
```

**curl:**
```bash
curl -X DELETE http://localhost:8000/items/1 \
  -H "Authorization: Bearer <access_token>"
```

---

## 10. Get Item Statistics

```
GET /items/stats
```

**Auth:** ✅ Required

**Response 200:**
```json
{
  "total_items": 10,
  "total_value": 75000000.0,
  "avg_price": 7500000.0,
  "avg_quantity": 4.5,
  "low_stock": 3
}
```

**Keterangan:**
- `total_items`: total jumlah item di database
- `total_value`: total nilai inventory (`price × quantity` untuk semua item)
- `avg_price`: rata-rata harga item
- `avg_quantity`: rata-rata quantity item
- `low_stock`: jumlah item dengan `quantity < 10`

**curl:**
```bash
curl http://localhost:8000/items/stats \
  -H "Authorization: Bearer <access_token>"
```

---

## 11. Team Info

```
GET /team
```

**Auth:** Tidak diperlukan

**Response 200:**
```json
{
  "team": "cloud-team-nyawit",
  "members": [
    {"name": "Muchlis Wahyu Saputra", "nim": "10231054", "role": "Lead Backend"},
    {"name": "Ranaya Chintya Mahitsa", "nim": "10231078", "role": "Lead Frontend"},
    {"name": "Ahmad Baihaqi", "nim": "10221063", "role": "Lead DevOps"},
    {"name": "Az-Zahra Atikah Nurhaliza", "nim": "10231022", "role": "Lead QA & Docs"}
  ]
}
```

**curl:**
```bash
curl http://localhost:8000/team
```

---

## 🔁 Alur Penggunaan API (End-to-End)

```
1. Register   → POST /auth/register
2. Login      → POST /auth/login  (simpan access_token)
3. CRUD Items → GET/POST/PUT/DELETE /items
               (sertakan header: Authorization: Bearer <token>)
4. Stats      → GET /items/stats
5. Profile    → GET /auth/me
```

---

## ❌ Error Codes Umum

| HTTP Status | Artinya | Contoh Kasus |
|-------------|---------|--------------|
| 400 | Bad Request | Email sudah terdaftar |
| 401 | Unauthorized | Token tidak ada/expired/invalid |
| 403 | Forbidden | Akun tidak aktif |
| 404 | Not Found | Item ID tidak ditemukan |
| 422 | Validation Error | Request body tidak sesuai schema |

---

*Dokumen ini dibuat oleh Lead CI/CD — berdasarkan kode backend versi `0.5.0`*
