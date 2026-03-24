# 📖 Setup Guide — SICURE Full-Stack App

Panduan lengkap dari clone repository sampai aplikasi berjalan.  
Dokumen ini ditujukan untuk siapa saja yang baru pertama kali melihat proyek ini.

---

## ✅ Prasyarat

Pastikan software berikut sudah terinstal di komputer Anda:

| Software | Versi Minimum | Cek Versi |
|----------|--------------|-----------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| PostgreSQL | 14+ | `psql --version` |
| Git | 2.x | `git --version` |

---

## 1. Clone Repository

```bash
git clone <URL_REPOSITORY_TIM>
cd cc-kelompok-nyawit_1
```

---

## 2. Setup Database PostgreSQL

### 2.1 Masuk ke psql
```bash
psql -U postgres
```

### 2.2 Buat Database
```sql
CREATE DATABASE sicure;
\q
```

---

## 3. Setup Backend

### 3.1 Masuk ke folder backend
```bash
cd backend
```

### 3.2 Buat Virtual Environment
```bash
python -m venv venv

# Aktivasi (Linux/macOS)
source venv/bin/activate

# Aktivasi (Windows)
venv\Scripts\activate
```

### 3.3 Install Dependencies
```bash
pip install -r requirements.txt
```

### 3.4 Konfigurasi Environment Variables

Salin file contoh dan isi nilainya:
```bash
cp .env.example .env
```

Edit file `.env`:
```env
# Database
DATABASE_URL=postgresql://postgres:PASSWORD_ANDA@localhost:5432/sicure

# JWT — generate dengan: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=isi-dengan-random-string-minimal-32-karakter
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS — daftar origin frontend yang diizinkan
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

> 💡 **Generate SECRET_KEY:**
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 3.5 Jalankan Backend

```bash
uvicorn main:app --reload --port 8000
```

Backend berjalan di: `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

---

## 4. Setup Frontend

### 4.1 Buka terminal baru, masuk ke folder frontend

```bash
cd frontend
```

### 4.2 Install Dependencies
```bash
npm install
```

### 4.3 Konfigurasi Environment Variables

```bash
cp .env.example .env
```

File `.env` sudah terisi dengan nilai default:
```env
VITE_API_URL=http://localhost:8000
```

> Jika backend berjalan di port/host berbeda, ubah nilai `VITE_API_URL` sesuai kebutuhan.

### 4.4 Jalankan Frontend
```bash
npm run dev
```

Frontend berjalan di: `http://localhost:5173`

---

## 5. Verifikasi Aplikasi Berjalan

Buka browser dan akses `http://localhost:5173`. Anda akan melihat halaman **Login**.

### Checklist Verifikasi

- [ ] Backend: `http://localhost:8000/health` mengembalikan `{"status": "healthy"}`
- [ ] Swagger UI: `http://localhost:8000/docs` dapat diakses
- [ ] Frontend: `http://localhost:5173` menampilkan halaman Login
- [ ] Register user baru berhasil
- [ ] Login berhasil → masuk ke halaman utama CRUD
- [ ] CRUD item berfungsi (create, read, update, delete)
- [ ] Logout → kembali ke halaman Login

---

## 6. Struktur Folder Proyek

```
cc-kelompok-nyawit_1/
├── backend/
│   ├── main.py          # Entry point FastAPI, routing
│   ├── auth.py          # JWT utilities
│   ├── database.py      # Koneksi database SQLAlchemy
│   ├── models.py        # Model Item & User
│   ├── schemas.py       # Pydantic schemas (validasi)
│   ├── crud.py          # Database operations
│   ├── requirements.txt # Python dependencies
│   ├── .env             # Konfigurasi (TIDAK di-commit)
│   └── .env.example     # Template .env (di-commit)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Root component + auth state
│   │   ├── components/      # React components
│   │   │   ├── LoginPage.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── ItemForm.jsx
│   │   │   ├── ItemList.jsx
│   │   │   └── ItemCard.jsx
│   │   └── services/
│   │       └── api.js       # API layer + token management
│   ├── .env             # Konfigurasi (TIDAK di-commit)
│   └── .env.example     # Template .env (di-commit)
├── docs/                # Dokumentasi tim
├── .gitignore
└── README.md
```

---

## 7. Troubleshooting Umum

| Masalah | Kemungkinan Penyebab | Solusi |
|---------|---------------------|--------|
| `CORS Error` | `ALLOWED_ORIGINS` tidak termasuk URL frontend | Tambahkan URL frontend ke `ALLOWED_ORIGINS` di `.env` backend |
| `401 Unauthorized` | Token expired atau tidak valid | Logout dan login ulang |
| `connection refused` (DB) | PostgreSQL tidak berjalan | Jalankan PostgreSQL service |
| `ModuleNotFoundError` | Dependency belum terinstall | Jalankan `pip install -r requirements.txt` di venv |
| `VITE_API_URL` tidak terbaca | Frontend belum restart setelah edit `.env` | Restart `npm run dev` |

---

## 8. Catatan Keamanan

- File `.env` **tidak pernah** di-commit ke Git (sudah ada di `.gitignore`)
- Gunakan `SECRET_KEY` yang kuat dan unik di setiap environment
- Untuk production: ganti `ALLOWED_ORIGINS` dengan domain production yang sebenarnya

---

*Dokumen ini dibuat oleh Lead DevOps — Ahmad Baihaqi (10221063)*
