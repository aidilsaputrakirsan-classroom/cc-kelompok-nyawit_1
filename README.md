# ☁️ Cloud App - [SICURE Sistem Information Procurement]

# Cloud App – SICURE (Sistem Information Procurement)

SICURE (Sistem Information Procurement) merupakan aplikasi berbasis cloud yang dirancang untuk membantu organisasi dalam mengelola arus keuangan serta proses pengadaan barang secara digital, terstruktur, dan transparan. Sistem ini memungkinkan pencatatan arus kas masuk dan kas keluar secara real-time, sekaligus mendukung proses pengajuan dan persetujuan pengadaan (procurement) dalam satu platform terintegrasi.

Aplikasi ini ditujukan untuk organisasi seperti himpunan mahasiswa, UKM, komunitas, atau unit kegiatan lainnya yang membutuhkan sistem pencatatan keuangan dan pengadaan yang lebih tertib. Dengan digitalisasi melalui SICURE, proses administrasi menjadi lebih efisien, risiko kesalahan pencatatan dapat diminimalkan, serta transparansi keuangan dapat ditingkatkan.

Melalui sistem berbasis cloud, data dapat diakses oleh pihak yang berwenang kapan saja dan di mana saja. Selain itu, SICURE mendukung mekanisme monitoring dan pelaporan yang membantu organisasi dalam mengambil keputusan yang lebih tepat terkait pengelolaan dana dan pengadaan barang.

---

## Fitur Sistem

Berikut penjelasan detail dan terstruktur mengenai fitur-fitur utama dalam aplikasi SICURE yang mendukung pemantauan arus kas serta optimasi proses pengadaan (procurement).

## 1. Dashboard Keuangan (Financial Dashboard)

### Fungsi dan Manfaat
Menyediakan gambaran kondisi keuangan organisasi secara real-time sehingga manajemen dapat memantau arus kas, posisi saldo, serta kesehatan keuangan tanpa harus membuka laporan detail.

### Detail Fitur
- Grafik arus kas masuk dan keluar (harian, bulanan, tahunan)
- Total saldo kas saat ini
- Total piutang dan utang
- Pengeluaran terbesar per kategori
- Perbandingan realisasi dengan anggaran
- Indikator kesehatan keuangan (cash ratio, burn rate)

---

## 2. Manajemen Arus Kas (Cash Flow Management)

### Fungsi dan Manfaat
Mencatat seluruh transaksi keuangan secara terpusat untuk menghindari kesalahan pencatatan, kehilangan data, serta meningkatkan transparansi keuangan organisasi.

### Detail Fitur
- Input pemasukan (donasi, penjualan, iuran, dll.)
- Input pengeluaran (operasional, pengadaan, dll.)
- Klasifikasi transaksi berdasarkan kategori
- Upload bukti transaksi
- Edit dan histori perubahan transaksi
- Rekonsiliasi dengan mutasi bank
- Penandaan transaksi (verified/unverified)

---

## 3. Pengelolaan Faktur (Invoice Management)

### Fungsi dan Manfaat
Mengatur faktur masuk dan keluar agar pembayaran dapat dilakukan tepat waktu serta mencegah keterlambatan dan denda.

### Detail Fitur
- Input data faktur (nomor, vendor, nominal, tanggal)
- Status faktur (draft, approved, paid, overdue)
- Reminder sebelum jatuh tempo
- Tracking pembayaran parsial
- Integrasi dengan sistem kas
- Riwayat pembayaran

---

## 4. Modul Pengadaan (Procurement Management)

### Fungsi dan Manfaat
Mengelola proses pembelian barang atau jasa secara sistematis dan transparan untuk mencegah pembelian tanpa persetujuan resmi.

### Detail Fitur
- Form pengajuan pengadaan (nama barang, estimasi harga, vendor, alasan kebutuhan)
- Workflow approval bertingkat
- Status tracking (submitted, approved, rejected, completed)
- Upload dokumen pendukung
- Perbandingan penawaran vendor
- Konversi menjadi Purchase Order (PO)

---

## 5. Manajemen Vendor

### Fungsi dan Manfaat
Menyimpan dan mengevaluasi data vendor untuk membantu organisasi memilih vendor terbaik dan meningkatkan efisiensi biaya.

### Detail Fitur
- Database vendor
- Riwayat transaksi per vendor
- Nilai kontrak dan histori pembayaran
- Evaluasi performa vendor
- Blacklist vendor (opsional)

---

## 6. Manajemen Kontrak

### Fungsi dan Manfaat
Mengontrol masa berlaku dan nilai kontrak agar tidak terjadi kontrak berakhir tanpa evaluasi atau perpanjangan.

### Detail Fitur
- Penyimpanan dokumen kontrak digital
- Informasi nilai dan periode kontrak
- Notifikasi sebelum kontrak berakhir
- Monitoring sisa nilai kontrak
- Riwayat perpanjangan

---

## 7. Budgeting dan Budget Control

### Fungsi dan Manfaat
Mengontrol penggunaan anggaran agar tidak melebihi batas yang ditetapkan serta menjaga stabilitas keuangan organisasi.

### Detail Fitur
- Input anggaran tahunan/bulanan
- Anggaran per divisi atau proyek
- Monitoring realisasi vs anggaran
- Alert jika mendekati batas
- Blokir otomatis (opsional)
- Forecast pengeluaran

---

## 8. Reporting dan Analisis

### Fungsi dan Manfaat
Menyediakan laporan komprehensif untuk mendukung audit serta pengambilan keputusan yang lebih akurat.

### Detail Fitur
- Laporan arus kas
- Laporan laba rugi
- Neraca
- Laporan pengadaan
- Grafik tren pembelian
- Export ke PDF/Excel
- Filter berdasarkan tanggal/divisi

---

## 9. Notifikasi dan Reminder System

### Fungsi dan Manfaat
Memberikan pengingat otomatis untuk mengurangi kelalaian dan meningkatkan efisiensi kerja.

### Detail Fitur
- Reminder jatuh tempo faktur
- Notifikasi approval pengadaan
- Alert saldo minimum
- Reminder kontrak hampir habis
- Notifikasi email dan dalam aplikasi

---

## 10. Manajemen Akses dan Keamanan

### Fungsi dan Manfaat
Menjamin keamanan serta akuntabilitas sistem melalui pengaturan hak akses dan perlindungan data.

### Detail Fitur
- Role-based access control
- Audit log aktivitas pengguna
- Enkripsi data sensitif
- Backup otomatis
- Two-factor authentication (opsional)

---


## 👥 Tim

| Nama | NIM | Peran |
|------|------|--------|
| Muchlis Wahyu Saputra | 10231054 | Lead Backend |
| Ranaya Chintya Mahitsa | 10231078 | Lead Frontend |
| Ahmad Baihaqi | 10221063 | Lead DevOps  |
| Az-Zahra Atikah Nurhaliza | 10231022 | Lead QA & Docs |

---

## 🛠️ Tech Stack

| Teknologi | Fungsi |
|------------|--------|
| FastAPI | Backend REST API |
| React (Vite) | Frontend SPA |
| PostgreSQL | Database |
| Docker | Containerization |
| GitHub Actions | CI/CD |
| Railway / Render | Cloud Deployment |

---

## 🏗️ Architecture

[React Frontend] <--HTTP--> [FastAPI Backend] <--SQL--> [PostgreSQL]

_(Diagram ini akan berkembang setiap minggu)_
---

## 🚀 Getting Started

## Prasyarat
- Python 3.10+
- Node.js 18+
- Git

---

## Backend 
```bash 
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 📅 Roadmap

| Minggu | Target                  | Status |
|--------|--------------------------|--------|
| 1      | Setup & Hello World      | ✅     |
| 2      | REST API + Database      | ⬜     |
| 3      | React Frontend           | ⬜     |
| 4      | Full-Stack Integration   | ⬜     |
| 5-7    | Docker & Compose         | ⬜     |
| 8      | UTS Demo                 | ⬜     |
| 9-11   | CI/CD Pipeline           | ⬜     |
| 12-14  | Microservices            | ⬜     |
| 15-16  | Final & UAS              | ⬜     |

--- 

