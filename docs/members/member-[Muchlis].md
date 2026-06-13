# Reflection Paper — Muchlis Wahyu Saputra

- **NIM:** 10231054
- **Peran:** Lead Backend
- **Proyek:** SiCure — Sistem Informasi Procurement

> Reflection ini bersifat **analitis**, bukan deskriptif: jelaskan *keputusan teknis*,
> *kesulitan*, dan *pelajaran* — bukan sekadar daftar "saya mengerjakan X". Target 1–2 halaman.
> Ganti seluruh teks miring di bawah dengan tulisanmu sendiri.

## 1. Ringkasan Kontribusi
*Ringkas 3–5 kalimat peran utamamu di backend (mis. desain API, model data,
auth JWT, aturan bisnis vendor quote, observability/logging).*

## 2. Keputusan Teknis & Alasannya
*Pilih 2–3 keputusan dan jelaskan "kenapa", bukan hanya "apa". Contoh arah:*
- *Kenapa FastAPI + SQLAlchemy async (bukan sync)? Apa trade-off-nya?*
- *Kenapa envelope response `{success, data, message}` diseragamkan?*
- *Kenapa JWT memakai access + refresh token dan token blacklist untuk logout?*
- *Kenapa structured logging JSON + correlation ID dipilih untuk observability?*

## 3. Kesulitan & Cara Mengatasi
*Ceritakan masalah nyata (mis. transaksi atomik saat upload gagal, migrasi Alembic,
testing async dengan SQLite) dan bagaimana kamu mendiagnosis & menyelesaikannya.*

## 4. Pelajaran yang Diambil
*Apa yang akan kamu lakukan berbeda? Pelajaran tentang desain API, keamanan,
atau kualitas kode.*

## 5. Pemahaman Sistem Secara Keseluruhan
*Jelaskan alur request user → backend → database, peran tiap modul, dan
bagaimana CI/CD serta deployment Railway bekerja — termasuk bagian yang bukan
kamu kerjakan (frontend, DevOps, QA), karena viva bersifat individual.*
