# Reflection Paper — Ahmad Baihaqi

- **NIM:** 10221063
- **Peran:** Lead DevOps
- **Proyek:** SiCure — Sistem Informasi Procurement

> Reflection ini bersifat **analitis**, bukan deskriptif: jelaskan *keputusan teknis*,
> *kesulitan*, dan *pelajaran*. Target 1–2 halaman. Ganti teks miring dengan tulisanmu.

## 1. Ringkasan Kontribusi
*Ringkas peran utamamu di DevOps (mis. workflow CI, orkestrasi container,
networking & volume Docker, konfigurasi nginx, reliability patterns).*

## 2. Keputusan Teknis & Alasannya
*Pilih 2–3 keputusan dan jelaskan "kenapa". Contoh arah:*
- *Kenapa job CI dipisah (test-backend, test-frontend, build-docker) dengan `needs`?*
- *Kenapa testing CI memakai SQLite in-memory — apa untung/ruginya vs PostgreSQL?*
- *Kenapa Docker network & named volume dipakai, dan apa peran healthcheck di compose?*
- *Pelajaran dari reliability patterns (retry, timeout, circuit breaker) saat fase microservices.*

## 3. Kesulitan & Cara Mengatasi
*Masalah nyata (mis. konflik merge, pipeline flaky, koordinasi environment dev vs prod)
dan bagaimana diselesaikan.*

## 4. Pelajaran yang Diambil
*Apa yang akan kamu lakukan berbeda terkait otomasi, testing, atau resiliensi?*

## 5. Pemahaman Sistem Secara Keseluruhan
*Jelaskan alur request user → backend → database, peran tiap stage CI/CD,
cara deploy Railway, dan trade-off monolith vs microservices — termasuk bagian
backend/frontend/QA, karena viva bersifat individual.*
