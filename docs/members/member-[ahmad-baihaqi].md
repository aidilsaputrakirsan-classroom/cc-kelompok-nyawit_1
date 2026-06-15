# Reflection Paper — Ahmad Baihaqi

- **NIM:** 10221063
- **Peran:** Lead DevOps
- **Proyek:** SiCure — Sistem Informasi Procurement

## 1. Ringkasan Kontribusi

Sebagai Lead DevOps, saya bertanggung jawab memastikan proses pengembangan, pengujian, dan deployment aplikasi SiCure dapat berjalan secara konsisten dan otomatis. Tugas utama saya meliputi pengelolaan workflow CI menggunakan GitHub Actions, konfigurasi container menggunakan Docker, pengaturan jaringan dan volume untuk komunikasi antar layanan, serta membantu proses deployment aplikasi ke Railway.

Selain itu, saya juga berperan dalam menjaga stabilitas lingkungan pengembangan agar backend, frontend, dan database dapat berjalan dengan konfigurasi yang seragam pada setiap anggota tim. Dengan adanya otomatisasi dan standarisasi lingkungan kerja, proses integrasi dan pengujian dapat dilakukan dengan lebih cepat dan mengurangi risiko kesalahan konfigurasi.

## 2. Keputusan Teknis dan Alasannya

Salah satu keputusan yang saya ambil adalah memisahkan pipeline CI menjadi beberapa job seperti `test-backend`, `test-frontend`, dan `build-docker`. Setiap job memiliki tanggung jawab yang berbeda sehingga proses pengujian menjadi lebih terstruktur. Selain itu, penggunaan `needs` memastikan proses build hanya berjalan ketika seluruh pengujian berhasil. Pendekatan ini membantu tim menemukan sumber masalah dengan lebih cepat ketika terjadi kegagalan pada pipeline.

Keputusan kedua adalah menggunakan SQLite in-memory pada proses testing CI. Penggunaan SQLite membuat proses pengujian lebih cepat karena tidak memerlukan service database tambahan. Hal ini mempercepat feedback saat developer melakukan perubahan kode. Namun, saya juga menyadari bahwa terdapat perbedaan perilaku antara SQLite dan PostgreSQL sehingga beberapa pengujian tetap perlu dilakukan pada lingkungan yang lebih mendekati production.

Saya juga memutuskan menggunakan Docker network dan named volume pada lingkungan pengembangan. Docker network memudahkan komunikasi antar container tanpa perlu konfigurasi alamat IP secara manual, sedangkan named volume memastikan data tetap tersimpan meskipun container dihentikan atau dibuat ulang. Selain itu, healthcheck digunakan untuk memastikan setiap service benar-benar siap sebelum digunakan oleh service lain sehingga mengurangi kegagalan saat startup aplikasi.

Dari pengalaman awal mencoba pendekatan microservices, saya juga belajar mengenai pentingnya reliability patterns seperti retry dan timeout. Meskipun pada akhirnya sistem menggunakan pendekatan monolith, pemahaman tersebut membantu saya memahami bagaimana sistem dapat tetap berjalan ketika terjadi gangguan komunikasi antar layanan.

## 3. Kesulitan dan Cara Mengatasi

Salah satu kesulitan yang saya hadapi adalah konflik merge pada konfigurasi CI dan Docker ketika beberapa anggota tim melakukan perubahan secara bersamaan. Konflik ini sering menyebabkan workflow gagal dijalankan atau konfigurasi tidak sesuai harapan. Untuk mengatasinya, kami menerapkan proses review melalui pull request sehingga perubahan dapat diperiksa sebelum digabungkan ke branch utama.

Saya juga menghadapi masalah pipeline yang tidak selalu menghasilkan hasil yang konsisten. Terkadang pengujian berhasil di komputer lokal tetapi gagal pada GitHub Actions karena perbedaan environment. Untuk mengatasi hal tersebut, saya berusaha menyamakan konfigurasi lingkungan pengembangan dengan lingkungan CI menggunakan Docker serta memastikan dependency yang digunakan memiliki versi yang jelas.

Tantangan lainnya adalah koordinasi antara lingkungan development dan production. Beberapa konfigurasi seperti environment variable dan URL service berbeda antara kedua lingkungan tersebut. Untuk mengurangi kesalahan konfigurasi, saya mendokumentasikan seluruh variabel yang diperlukan dan menggunakan file contoh konfigurasi agar anggota tim dapat menyiapkan environment dengan lebih mudah.

Selain masalah teknis, koordinasi antar anggota tim juga menjadi tantangan tersendiri. Ketika ada perubahan pada backend atau frontend, konfigurasi DevOps sering kali perlu ikut disesuaikan. Oleh karena itu, komunikasi dan dokumentasi menjadi hal yang sangat penting agar seluruh anggota memiliki pemahaman yang sama mengenai perubahan yang dilakukan.

## 4. Pelajaran yang Diambil

Melalui proyek ini saya memahami bahwa DevOps bukan hanya tentang deployment, tetapi juga tentang membangun proses yang dapat diandalkan dan mudah digunakan oleh seluruh tim. Otomatisasi melalui CI/CD sangat membantu mengurangi pekerjaan manual dan meningkatkan kualitas perangkat lunak.

Saya juga belajar bahwa stabilitas lingkungan pengembangan sangat berpengaruh terhadap produktivitas tim. Docker membantu menciptakan lingkungan yang konsisten sehingga masalah yang muncul akibat perbedaan konfigurasi dapat diminimalkan.

Selain itu, saya menyadari pentingnya membangun sistem yang memiliki kemampuan pemulihan ketika terjadi kegagalan. Ke depannya, saya ingin lebih banyak mempelajari monitoring, logging, dan observability agar masalah dapat dideteksi lebih cepat sebelum berdampak pada pengguna.

Jika mengerjakan proyek serupa di masa depan, saya akan lebih awal menerapkan standar otomasi dan dokumentasi sehingga proses integrasi dapat berjalan lebih lancar sejak awal pengembangan.

## 5. Pemahaman Sistem Secara Keseluruhan

SiCure merupakan sistem procurement berbasis web yang terdiri dari frontend, backend, database, serta infrastruktur deployment. Pengguna berinteraksi melalui frontend untuk melakukan berbagai aktivitas seperti membuat Purchase Requisition atau melihat status pengadaan. Frontend kemudian mengirim request ke backend melalui API.

Backend bertugas memproses request, melakukan validasi, menjalankan aturan bisnis, dan berinteraksi dengan database untuk menyimpan maupun mengambil data. Setelah proses selesai, backend mengirimkan response yang akan ditampilkan kembali pada frontend.

Pada proses CI/CD, setiap perubahan kode yang dikirim ke repository akan memicu GitHub Actions. Pipeline akan menjalankan pengujian backend dan frontend terlebih dahulu. Jika seluruh pengujian berhasil, proses build dapat dilanjutkan. Setelah kode digabungkan ke branch utama, Railway akan melakukan deployment secara otomatis sehingga perubahan dapat segera tersedia pada lingkungan production.

Data aplikasi tetap tersimpan meskipun container mengalami restart karena database menggunakan penyimpanan persisten yang terpisah dari container aplikasi. Dengan demikian, proses deployment tidak menyebabkan kehilangan data pengguna.

Selama pengembangan, tim sempat mempertimbangkan pendekatan microservices. Namun, setelah mempertimbangkan kompleksitas pengelolaan layanan, komunikasi antar service, dan keterbatasan ruang lingkup proyek, pendekatan monolith dipilih karena lebih sederhana dan lebih mudah dikelola. Untuk ukuran proyek SiCure, pendekatan ini memberikan keseimbangan yang baik antara kemudahan pengembangan dan kebutuhan sistem.

Dalam keseluruhan proyek, frontend bertanggung jawab pada antarmuka pengguna, backend menangani logika bisnis dan data, QA memastikan kualitas sistem melalui pengujian, sedangkan DevOps mendukung proses build, deployment, dan infrastruktur. Kolaborasi seluruh peran tersebut menjadi faktor utama dalam keberhasilan pengembangan aplikasi SiCure.