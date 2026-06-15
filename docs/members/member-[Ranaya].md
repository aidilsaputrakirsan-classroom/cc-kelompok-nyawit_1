# Reflection Paper — Ranaya Chintya Mahitsa

- **NIM:** 10231078
- **Peran:** Lead Frontend
- **Proyek:** SiCure — Sistem Informasi Procurement

> Reflection ini bersifat **analitis**, bukan deskriptif: jelaskan *keputusan teknis*,
> *kesulitan*, dan *pelajaran*. Target 1–2 halaman. Ganti teks miring dengan tulisanmu.

## 1. Ringkasan Kontribusi
Sebagai Lead Frontend, kontribusi utama saya adalah merapikan arsitektur antarmuka React + TypeScript agar mudah dikembangkan oleh tim. Saya memusatkan pengelolaan state autentikasi (melalui context) dan menguatkan integrasi API menggunakan Axios supaya alur procurement (PR → PO → GRN) bisa ditampilkan dengan konsisten di berbagai halaman. Saya juga menyiapkan pola penanganan error dan verifikasi UI melalui pengujian komponen/utility agar perubahan tidak merusak experience pengguna.

## 2. Keputusan Teknis & Alasannya
Beberapa keputusan teknis yang saya ambil:

1) **TypeScript diutamakan untuk kontrak data dan refactor yang aman**
   Kami memakai TypeScript untuk mempertegas bentuk data dari backend (mis. skema PR/PO/GRN dan payload upload). Dampaknya, saat ada perubahan kecil di response API, compiler membantu mendeteksi mismatch lebih cepat sehingga bug di UI lebih sedikit.

2) **State autentikasi dan kondisi layanan dipusatkan lewat Context**
   Token dan status login (termasuk skenario “auth down”) seharusnya tidak diulang di setiap halaman. Dengan context, komponen halaman cukup membaca state dan menampilkan UI yang sesuai. Keputusan ini mengurangi duplikasi logika (mis. pengecekan token) serta membuat testing lebih terarah.

3) **Pola error handling global berbasis interceptor Axios**
   Karena sebagian besar interaksi UI adalah request API, interceptor memberi tempat sentral untuk mengelola respons error seperti HTTP 401/403/503. Dengan begitu, UI bisa merespons secara seragam (mis. menampilkan banner “sementara tidak tersedia” dan menyediakan tombol *Retry*), bukan menyebarkan penanganan error di tiap komponen.

## 3. Kesulitan & Cara Mengatasi
Kesulitan yang paling terasa berada pada aspek “ketahanan UI” terhadap kegagalan request dan kompleksitas integrasi multi-layanan.

- **Konsistensi penanganan error lintas endpoint**
  Error bisa memiliki bentuk payload berbeda-beda dari gateway/backend. Solusi saya adalah membuat utilitas yang menormalisasi pesan error dan menetapkan aturan UI yang seragam (mis. cara tampilkan pesan, kapan toast dipicu, dan kapan UI butuh interaksi seperti tombol Retry).

- **Upload multipart (vendor quote/GRN) dan validasi**
  Saat payload upload berbeda antara browser dan backend (boundary multipart, field name, tipe file), error yang muncul sering sulit ditelusuri. Saya mengatasinya dengan memastikan skema request di frontend sesuai kontrak backend, menambahkan error surfacing yang lebih jelas, dan menjaga feedback UI agar user paham langkah berikutnya.

- **Routing SPA di belakang nginx**
  Untuk menghindari 404 saat refresh halaman route tertentu, nginx perlu merutekan semua path ke entrypoint SPA. Ini penting karena aplikasi procurement punya banyak halaman detail; jika routing salah, user akan stuck hanya karena refresh.

## 4. Pelajaran yang Diambil
Ke depan, saya akan lebih menekankan pemisahan tanggung jawab: request layer (Axios/interceptor), domain layer (fungsi/transformasi data), dan presentation layer (komponen halaman). Dari sisi UX, saya juga belajar bahwa error handling bukan sekadar “menampilkan pesan”, tapi harus memberi *next action* yang jelas (mis. *Retry*, atau panduan langkah saat layanan tertentu tidak tersedia). Dengan pendekatan ini, sistem terasa lebih stabil meski backend/gateway tidak ideal.

## 5. Pemahaman Sistem Secara Keseluruhan
Alur request user dimulai dari **frontend** yang memanggil endpoint melalui **gateway/nginx**. Gateway meneruskan request ke **backend service** terkait (auth/procurement). Backend kemudian menjalankan validasi, mengakses database, dan mengembalikan response ke frontend. Pada modul procurement, request mengikuti rantai data: pengguna mengajukan PR, sistem memproses PO, lalu vendor quote/GRN dipakai untuk melengkapi transaksi.

Dari sisi deploy, proyek dijalankan di lingkungan seperti Railway dengan konfigurasi CI/CD: pipeline membangun image (backend/frontend), menjalankan test (unit/integration), lalu mem-publish perubahan. Bagian QA/DevOps menjadi krusial karena perubahan kecil di skema atau rute bisa memicu error di UI; karena itu saya memperhatikan integrasi kontrak API dan menyiapkan skenario error handling agar sistem tetap usable.

## 4. Pelajaran yang Diambil
*Apa yang akan kamu lakukan berbeda dari sisi UX/arsitektur frontend?*

## 5. Pemahaman Sistem Secara Keseluruhan
*Jelaskan alur request user → gateway/nginx → backend → database, peran tiap service,
cara deploy ke Railway, dan cara kerja CI/CD — termasuk bagian backend/DevOps/QA,
karena viva bersifat individual.*
