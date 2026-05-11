# Testing Guide

Dokumen ini digunakan sebagai panduan testing untuk backend dan frontend project, termasuk cara menjalankan test secara lokal, membaca CI log, debugging test failure, dan menambahkan test baru.

---

## 1. Prerequisites

Sebelum menjalankan testing, pastikan beberapa kebutuhan berikut sudah tersedia:

- Python dan Node.js sudah terinstall
- Dependency project sudah di-install
- File `.env` sudah dikonfigurasi
- Database atau service pendukung sudah berjalan jika diperlukan

---

## 2. Menjalankan Test Backend

Masuk ke folder backend terlebih dahulu:

```bash
cd backend
```

Install dependency jika belum:

```bash
pip install -r requirements.txt
```

Jalankan seluruh test backend:

```bash
pytest
```

Menjalankan test dengan coverage:

```bash
pytest --cov=app
```

Menjalankan file test tertentu:

```bash
pytest tests/test_items.py
```

Contoh hasil test berhasil:

```bash
================= test session starts =================
15 passed in 2.10s
```

---

## 3. Menjalankan Test Frontend

Masuk ke folder frontend:

```bash
cd frontend
```

Install dependency:

```bash
npm install
```

Jalankan seluruh test frontend:

```bash
npm test
```

Menjalankan test coverage:

```bash
npm run test -- --coverage
```

Menjalankan test tertentu:

```bash
npm test SearchBar
```

Contoh hasil test berhasil:

```bash
PASS src/tests/SearchBar.test.jsx
PASS src/tests/ItemForm.test.jsx
```

---

## 4. Struktur Testing

Contoh struktur folder testing pada project:

```bash
backend/
└── tests/
    ├── test_items.py
    ├── test_stats.py
    └── test_pagination.py

frontend/
└── src/
    └── tests/
        ├── SearchBar.test.jsx
        ├── ItemForm.test.jsx
        └── ItemList.test.jsx
```

---

## 5. Cara Membaca CI Log

CI pipeline akan berjalan otomatis setiap terdapat push atau Pull Request pada repository.

Langkah melihat CI log:

1. Buka repository GitHub
2. Pilih tab **Actions**
3. Klik workflow yang berjalan
4. Pilih job yang ingin dilihat
5. Periksa bagian log yang gagal atau error

Biasanya error ditandai dengan warna merah dan pesan seperti:

```bash
FAILED tests/test_items.py
```

atau:

```bash
Test suite failed to run
```

Status pada CI:

| Status | Keterangan |
|--------|-------------|
| ✅ Success | Semua test berhasil |
| ❌ Failed | Ada test yang gagal |
| 🟡 Running | Test sedang berjalan |
| ⚪ Cancelled | Workflow dibatalkan |

---

## 6. Cara Debug Test Failure

Beberapa langkah debugging yang dapat dilakukan ketika test gagal:

### Backend

- Pastikan dependency sudah terinstall
- Pastikan database/service berjalan
- Jalankan test satu per satu
- Periksa endpoint dan response API
- Periksa detail error pada terminal

Contoh:

```bash
pytest tests/test_items.py -v
```

---

### Frontend

- Pastikan npm dependency sudah lengkap
- Periksa component yang error
- Jalankan test spesifik
- Gunakan console log sementara jika diperlukan

Contoh:

```bash
npm test SearchBar
```

Contoh debugging sederhana:

```javascript
console.log(response);
```

---

## 7. Cara Menambahkan Test Baru

### Backend

Tambahkan file test pada folder:

```bash
backend/tests/
```

Contoh penamaan file:

```bash
test_items.py
test_stats.py
```

Contoh test backend:

```python
def test_get_items():
    assert response.status_code == 200
```

---

### Frontend

Tambahkan file test pada folder:

```bash
frontend/src/tests/
```

Contoh penamaan file:

```bash
SearchBar.test.jsx
ItemForm.test.jsx
```

Contoh test frontend:

```javascript
test("renders search input", () => {
  render(<SearchBar />);
});
```

---

## 8. Best Practice Testing

- Gunakan nama test yang jelas dan mudah dipahami
- Test hanya satu fungsi utama pada setiap test
- Hindari duplikasi test
- Pastikan test dapat dijalankan ulang tanpa error
- Jalankan seluruh test sebelum melakukan push
- Update test jika terdapat perubahan fitur
- Gunakan coverage untuk memastikan kualitas testing

---

## 9. Testing Checklist

Sebelum melakukan merge Pull Request, pastikan:

- Semua test backend berhasil
- Semua test frontend berhasil
- Tidak ada error pada CI/CD
- Edge cases sudah diuji
- Coverage testing sudah diperiksa
- Dokumentasi testing sudah diperbarui

---

## 10. Penutup

Testing membantu memastikan aplikasi berjalan dengan baik dan mengurangi bug selama proses development maupun deployment. Dengan adanya CI dan test coverage, kualitas project dapat lebih terjaga dan proses kolaborasi tim menjadi lebih aman.