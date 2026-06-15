# Reflection Paper — Ranaya Chintya Mahitsa

- **NIM:** 10231078
- **Peran:** Lead Frontend
- **Proyek:** SiCure — Sistem Informasi Procurement

> Reflection ini bersifat **analitis**, bukan deskriptif: jelaskan keputusan teknis,
> kesulitan, dan pelajaran. Ganti teks miring dengan tulisanmu.

## 1. Ringkasan Kontribusi
Sebagai Lead Frontend, saya fokus pada arsitektur antarmuka React dengan TypeScript serta penataan state global untuk autentikasi dan kondisi layanan. Saya merancang struktur komponen agar dapat dipakai ulang lintas fitur (misalnya halaman detail PR/PO/GRN), mengoptimalkan integrasi API menggunakan Axios, dan menyusun alur tampilan yang mengikuti workflow procurement. Saya juga ikut memastikan kualitas melalui pengujian komponen/utility (Vitest) dan pembenahan boundary error supaya pengalaman pengguna tetap stabil saat terjadi kegagalan request.

## 2. Keputusan Teknis & Alasannya
*Pilih 2–3 keputusan dan jelaskan "kenapa". Contoh arah:*
- *Kenapa React 19 + TypeScript + Vite? Apa untungnya TypeScript di proyek tim?*
- *Bagaimana token JWT disimpan & dipakai di setiap request? Pertimbangan keamanannya?*
- *Kenapa `VITE_API_BASE_URL` di-bake saat build, dan konsekuensinya saat deploy?*
- *Bagaimana komponen reusable & custom hooks mengurangi duplikasi?*

## 3. Kesulitan & Cara Mengatasi
*Masalah nyata (mis. CORS antara frontend & backend, error handling response,
upload multipart vendor quote/GRN, routing SPA di nginx) dan solusinya.*

## 4. Pelajaran yang Diambil
*Apa yang akan kamu lakukan berbeda dari sisi UX/arsitektur frontend?*

## 5. Pemahaman Sistem Secara Keseluruhan
*Jelaskan alur request user → gateway/nginx → backend → database, peran tiap service,
cara deploy ke Railway, dan cara kerja CI/CD — termasuk bagian backend/DevOps/QA,
karena viva bersifat individual.*
