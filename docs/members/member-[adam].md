# Reflection Paper — Andi Adam Firdaus

- **NIM:** 10211014
- **Peran:** Lead DevOps
- **Proyek:** SiCure — Sistem Informasi Procurement

## 1. Ringkasan Kontribusi

Dalam proyek SiCure, saya bertanggung jawab pada aspek DevOps, mulai dari containerization, CI/CD, hingga deployment aplikasi ke cloud. Tugas utama saya meliputi pembuatan Dockerfile untuk backend dan frontend, konfigurasi Docker Compose untuk lingkungan pengembangan, penyusunan pipeline CI menggunakan GitHub Actions, serta deployment aplikasi ke Railway.

Selain itu, saya juga mengelola environment variables dan secrets yang digunakan pada lingkungan production, melakukan konfigurasi health check, serta memastikan proses deployment dapat berjalan secara otomatis setiap kali terdapat perubahan pada branch utama. Dengan adanya proses ini, tim dapat mengembangkan aplikasi dengan lebih konsisten dan mengurangi risiko kesalahan saat deployment.

## 2. Keputusan Teknis dan Alasannya

Salah satu keputusan yang saya ambil adalah menggunakan Docker untuk seluruh komponen aplikasi. Dengan Docker, lingkungan pengembangan setiap anggota tim menjadi lebih konsisten sehingga masalah perbedaan konfigurasi sistem operasi atau dependency dapat diminimalkan. Selain itu, Docker juga memudahkan proses deployment karena aplikasi yang dijalankan di lingkungan lokal memiliki konfigurasi yang serupa dengan lingkungan production.

Keputusan kedua adalah menggunakan Railway sebagai platform deployment dan memanfaatkan fitur auto-deploy yang terintegrasi langsung dengan GitHub. Dibandingkan membuat proses deployment manual melalui GitHub Actions, pendekatan ini lebih sederhana dan mudah dikelola. Setiap perubahan yang berhasil masuk ke branch main akan langsung memicu deployment secara otomatis sehingga proses rilis menjadi lebih cepat dan konsisten.

Keputusan lainnya adalah menerapkan optimasi Docker image menggunakan multi-stage build dan file `.dockerignore`. Tujuannya adalah mengurangi ukuran image serta mempercepat proses build dan deployment. Dengan memisahkan proses build dan runtime, hanya file yang benar-benar dibutuhkan yang akan masuk ke image production sehingga penggunaan resource menjadi lebih efisien.

Saya juga menerapkan health check pada aplikasi untuk memastikan service berjalan dengan baik setelah deployment. Jika terjadi kegagalan saat startup atau koneksi ke database bermasalah, kondisi tersebut dapat diketahui lebih cepat sehingga proses perbaikan dapat segera dilakukan.

## 3. Kesulitan dan Cara Mengatasi

Kesulitan terbesar yang saya hadapi adalah mempelajari GitHub Actions dan membangun pipeline CI/CD dari awal. Saya belum memiliki pengalaman sebelumnya sehingga perlu mempelajari struktur workflow, job, serta dependency antar proses. Untuk mengatasinya, saya mempelajari dokumentasi resmi GitHub Actions dan mencoba berbagai konfigurasi hingga pipeline dapat berjalan dengan stabil.

Masalah lain muncul saat deployment ke Railway. Pada awalnya frontend tidak dapat berkomunikasi dengan backend karena perbedaan domain dan konfigurasi CORS. Saya mengatasinya dengan mengatur environment variable untuk URL backend pada frontend serta menambahkan konfigurasi origin yang diizinkan pada backend.

Saya juga mengalami kegagalan build Docker akibat dependency yang belum tercantum dalam `requirements.txt`. Akibatnya, container backend gagal terhubung ke database saat dijalankan. Untuk mengatasi masalah tersebut, saya melakukan pengecekan ulang seluruh dependency dan memastikan proses pengujian berjalan melalui CI sebelum deployment dilakukan.

Selain itu, beberapa anggota tim mengalami kendala saat menjalankan Docker Compose karena perbedaan versi Docker dan konflik port pada komputer masing-masing. Untuk membantu mengatasi masalah tersebut, saya menyiapkan dokumentasi troubleshooting yang berisi langkah-langkah penyelesaian masalah umum.

## 4. Pelajaran yang Diambil

Melalui proyek ini saya memahami bahwa DevOps bukan hanya tentang melakukan deployment aplikasi, tetapi juga membangun proses yang otomatis, konsisten, dan dapat diandalkan. CI/CD membantu mendeteksi kesalahan lebih awal sehingga risiko masalah pada lingkungan production dapat dikurangi.

Saya juga belajar pentingnya menjaga kesamaan lingkungan antara development dan production. Docker memberikan manfaat besar dalam hal ini karena seluruh anggota tim dapat menjalankan aplikasi dengan konfigurasi yang sama.

Selain itu, saya menyadari bahwa dokumentasi teknis memiliki peran penting dalam mendukung proses DevOps. Dokumentasi yang baik membantu anggota tim memahami proses deployment, konfigurasi lingkungan, dan langkah-langkah penanganan masalah.

Ke depannya, saya ingin meningkatkan kemampuan dalam bidang observability, monitoring, dan container orchestration agar dapat mengelola sistem yang lebih kompleks dan berskala lebih besar.

## 5. Pemahaman Sistem Secara Keseluruhan

SiCure merupakan aplikasi procurement berbasis web yang terdiri dari frontend, backend, database, dan infrastruktur deployment. Ketika pengguna melakukan suatu aksi melalui frontend, request akan dikirim ke backend melalui API. Backend kemudian memproses data sesuai aturan bisnis dan berinteraksi dengan database untuk menyimpan atau mengambil informasi yang diperlukan. Setelah proses selesai, backend mengirimkan response kembali ke frontend untuk ditampilkan kepada pengguna.

Frontend bertugas menyediakan antarmuka pengguna dan menampilkan data dari backend. Backend bertanggung jawab menjalankan logika bisnis, validasi data, serta komunikasi dengan database. Database digunakan untuk menyimpan seluruh data transaksi dan informasi sistem secara persisten.

Pada proses CI/CD, setiap perubahan kode yang dikirim ke repository akan memicu GitHub Actions untuk menjalankan pengujian backend dan frontend. Jika seluruh pengujian berhasil, perubahan dapat digabungkan ke branch utama. Selanjutnya Railway akan mendeteksi perubahan tersebut dan melakukan deployment secara otomatis.

Data aplikasi tetap tersimpan meskipun container mengalami restart karena database menggunakan penyimpanan persisten yang terpisah dari container aplikasi. Dengan demikian, proses deployment atau restart service tidak menyebabkan hilangnya data pengguna.

Dalam proyek ini, backend, frontend, QA, dan DevOps saling mendukung satu sama lain. Backend menyediakan API, frontend mengimplementasikan antarmuka pengguna, QA memastikan kualitas sistem melalui pengujian, sedangkan DevOps memastikan aplikasi dapat dibangun, diuji, dan dideploy secara konsisten ke lingkungan production.