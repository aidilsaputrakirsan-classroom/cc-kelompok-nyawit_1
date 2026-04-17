# Perbandingan Docker Image Python

## Hasil Pengujian

Perintah yang digunakan untuk melihat ukuran Docker image:

docker images

| Image | Disk Usage | Content Size |
|-------|-----------|--------------|
| python:3.12 | 1.62 GB | 428 MB |
| python:3.12-slim | 179 MB | 45.4 MB |
| python:3.12-alpine | 75 MB | 18.7 MB |

## Analisis

Dari hasil pengujian, terlihat perbedaan ukuran yang cukup jauh antara ketiga image tersebut, baik dari sisi disk usage maupun content size.

- python:3.12 memiliki ukuran paling besar karena menggunakan base image lengkap dengan banyak library bawaan.
- python:3.12-slim lebih ringan karena hanya berisi komponen penting yang dibutuhkan untuk menjalankan Python.
- python:3.12-alpine adalah yang paling kecil karena menggunakan Alpine Linux yang lebih minimal.

Jika dilihat dari content size, perbedaannya juga cukup signifikan. Ini menunjukkan bahwa semakin minimal base image yang digunakan, semakin kecil resource yang dibutuhkan.

## Kesimpulan

Kalau dilihat dari ukuran, python:3.12-alpine memang paling ringan.

Namun untuk penggunaan dalam proyek ini, python:3.12-slim lebih disarankan karena ukurannya sudah cukup kecil dan biasanya lebih stabil serta lebih kompatibel dibandingkan alpine.

