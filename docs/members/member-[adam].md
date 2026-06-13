# Reflection Paper — Andi Adam Firdaus

- **NIM:** 10211014
- **Peran:** Lead DevOps
- **Proyek:** SiCure — Sistem Informasi Procurement

> Reflection ini bersifat **analitis**, bukan deskriptif: jelaskan *keputusan teknis*,
> *kesulitan*, dan *pelajaran*. Target 1–2 halaman. Ganti teks miring dengan tulisanmu.

## 1. Ringkasan Kontribusi
*Ringkas peran utamamu di DevOps (mis. Dockerfile & docker-compose, CI pipeline
GitHub Actions, deployment Railway, environment variables & secrets).*

## 2. Keputusan Teknis & Alasannya
*Pilih 2–3 keputusan dan jelaskan "kenapa". Contoh arah:*
- *Kenapa multi-stage build & layer caching? Dampaknya ke ukuran image & waktu build?*
- *Kenapa pindah dari DeployCC ke Railway, dan kenapa konsolidasi ke monolith?*
- *Kenapa deploy memakai auto-deploy Railway + verifikasi health di CI, bukan deploy via Actions?*
- *Bagaimana healthcheck & migrasi otomatis saat startup container dirancang?*

## 3. Kesulitan & Cara Mengatasi
*Masalah nyata (mis. port `$PORT` dinamis di Railway, koneksi DB, pipeline merah,
caching dependency) dan bagaimana kamu menyelesaikannya.*

## 4. Pelajaran yang Diambil
*Apa yang akan kamu lakukan berbeda terkait CI/CD, observability, atau biaya cloud?*

## 5. Pemahaman Sistem Secara Keseluruhan
*Jelaskan alur request user → backend → database, peran tiap komponen, cara CI/CD
bekerja end-to-end, dan bagaimana data tetap persisten saat container restart —
termasuk bagian backend/frontend/QA, karena viva bersifat individual.*
