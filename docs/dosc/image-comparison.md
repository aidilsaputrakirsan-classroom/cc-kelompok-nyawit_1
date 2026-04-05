# Perbandingan Docker Image Python

## Hasil Pengujian

Perintah yang digunakan untuk melihat ukuran Docker image:

```docker images```

| Image | Disk Usage | Content Size |
|-------|-----------|--------------|
| python:3.12 | 1.62 GB | 428 MB |
| python:3.12-slim | 179 MB | 45.4 MB |
| python:3.12-alpine | 75 MB | 18.7 MB |

## Analisis

Dari hasil pengujian, terlihat perbedaan ukuran yang cukup jauh antara ketiga image tersebut.

- python:3.12 punya ukuran paling besar karena menggunakan base image lengkap dengan banyak library bawaan.
- python:3.12-slim lebih ringan karena hanya berisi komponen penting yang dibutuhkan untuk menjalankan Python.
- python:3.12-alpine adalah yang paling kecil karena menggunakan Alpine Linux yang lebih minimal.

Perbedaan ini menunjukkan kalau pemilihan base image itu berpengaruh banget ke ukuran image dan juga proses build nantinya.

## Kesimpulan

Kalau dilihat dari ukuran, python:3.12-alpine memang paling ringan.

Tapi untuk penggunaan di proyek ini, python:3.12-slim lebih disarankan karena ukurannya sudah cukup kecil dan biasanya lebih aman dari segi kompatibilitas dibanding alpine.