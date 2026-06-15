# Reflection Paper — Az-Zahra Atikah Nurhaliza

- **NIM:** 10231022
- **Peran:** Lead QA & Docs
- **Proyek:** SiCure — Sistem Informasi Procurement

## 1. Ringkasan Kontribusi

Dalam proyek SiCure, saya bertanggung jawab pada proses Quality Assurance (QA) dan dokumentasi. Peran saya meliputi penyusunan skenario pengujian, pembuatan test case, pelaksanaan smoke testing, serta memastikan pengujian backend dan frontend dapat berjalan melalui CI. Selain itu, saya juga mengelola dokumentasi proyek seperti README, API contract, deployment guide, testing guide, dan laporan hasil pengujian.

Sebagai QA, saya berfokus memastikan fitur utama seperti pembuatan Purchase Request (PR), proses approval dan penerbitan Purchase Order (PO), upload Goods Receipt Note (GRN), hingga verifikasi berjalan sesuai kebutuhan sistem. Pada sisi dokumentasi, saya memastikan seluruh anggota tim memiliki referensi yang sama selama proses pengembangan.

## 2. Keputusan Teknis dan Alasannya

Salah satu keputusan yang saya ambil adalah membedakan pengujian unit test dan integration test. Unit test digunakan untuk memeriksa fungsi-fungsi kecil dan aturan bisnis tertentu secara terpisah, sedangkan integration test digunakan untuk memastikan beberapa komponen dapat bekerja bersama dalam satu alur proses. Dengan pemisahan ini, kesalahan dapat ditemukan lebih cepat dan lokasi masalah lebih mudah diidentifikasi.

Keputusan kedua adalah menetapkan target minimal coverage testing sebesar 40%. Angka ini dipilih sebagai target yang realistis mengingat keterbatasan waktu pengerjaan proyek. Meskipun belum mencakup seluruh kode, coverage tersebut cukup membantu memastikan bagian-bagian penting sistem telah diuji dan mengurangi risiko kesalahan saat proses integrasi.

Keputusan lainnya adalah menjadikan API contract sebagai acuan utama dalam pengembangan. Setiap perubahan endpoint harus disertai pembaruan dokumentasi API. Hal ini penting karena backend dan frontend dikerjakan oleh anggota yang berbeda sehingga diperlukan kesepakatan yang jelas mengenai format request dan response agar integrasi berjalan lancar.

Selain itu, saya juga menekankan pentingnya dokumentasi seperti README, diagram arsitektur, dan deployment guide. Dokumentasi yang baik mempermudah anggota tim memahami sistem serta membantu proses pemeliharaan di masa mendatang.

## 3. Kesulitan dan Cara Mengatasi

Kesulitan pertama yang saya hadapi adalah menjaga dokumentasi tetap konsisten dengan perubahan kode. Selama pengembangan, perubahan fitur sering terjadi sehingga dokumentasi mudah tertinggal. Untuk mengatasinya, saya mengingatkan agar setiap perubahan yang memengaruhi API atau alur sistem selalu disertai pembaruan dokumentasi.

Kesulitan kedua adalah keterbatasan waktu untuk melakukan regression testing menjelang deadline. Banyak fitur baru selesai mendekati waktu pengumpulan sehingga waktu pengujian menjadi sangat sempit. Solusi yang dilakukan adalah memprioritaskan pengujian pada alur utama sistem terlebih dahulu, sedangkan masalah yang belum sempat diperbaiki dicatat sebagai *known issues*.

Tantangan terbesar justru berasal dari komunikasi tim. Pada awal proyek, pembagian tugas kurang jelas sehingga beberapa pekerjaan dikerjakan lebih dari satu orang, sementara tugas lain belum tersentuh. Selain itu, respons komunikasi terkadang lambat sehingga proses integrasi tertunda. Untuk mengatasinya, tim mulai menggunakan Trello sebagai media pemantauan tugas dan melakukan koordinasi secara lebih rutin agar progres setiap anggota dapat terlihat dengan jelas.

## 4. Pelajaran yang Diambil

Dari proyek ini saya belajar bahwa pengujian tidak cukup hanya mengandalkan unit test. Integration test dan pengujian manual tetap diperlukan karena banyak masalah baru muncul ketika beberapa komponen sistem digabungkan.

Saya juga memahami bahwa dokumentasi bukan hanya formalitas, tetapi bagian penting dari proses pengembangan. Dokumentasi yang baik dapat mengurangi kesalahan komunikasi, mempercepat debugging, dan memudahkan anggota baru memahami sistem.

Selain itu, saya menyadari bahwa komunikasi tim memiliki pengaruh besar terhadap keberhasilan proyek. Ke depannya, saya akan lebih aktif melakukan koordinasi, memantau progres pekerjaan, dan memastikan setiap anggota memahami tanggung jawabnya masing-masing.

## 5. Pemahaman Sistem Secara Keseluruhan

SiCure merupakan sistem procurement berbasis web yang terdiri dari frontend, backend, database, dan layanan deployment. Alur sistem dimulai ketika pengguna mengakses frontend dan mengirimkan permintaan, seperti membuat Purchase Request. Request tersebut diteruskan ke backend melalui API. Backend kemudian memproses data sesuai aturan bisnis dan menyimpannya ke database. Setelah proses selesai, backend mengirimkan response kembali ke frontend untuk ditampilkan kepada pengguna.

Modul utama dalam sistem meliputi pengelolaan Purchase Request, vendor quotation, Purchase Order, Goods Receipt Note, dan proses verifikasi. Setiap modul saling terhubung untuk mendukung proses pengadaan dari awal hingga akhir.

Pada proses CI, setiap perubahan kode yang dikirim ke repository akan memicu proses otomatis untuk menjalankan unit test dan pemeriksaan lainnya. Dengan cara ini, kesalahan dapat ditemukan lebih awal sebelum kode digabungkan ke branch utama.

Untuk deployment, aplikasi di-host menggunakan Railway. Backend dan frontend dideploy sebagai layanan terpisah yang saling berkomunikasi melalui API. Pendekatan ini memudahkan proses pengelolaan, pembaruan sistem, dan pemantauan aplikasi setelah dirilis.