# Pengujian Ketahanan Sistem — SiCure

Dokumen ini mendefinisikan pendekatan pengujian **ketahanan sistem (reliability testing)** pada arsitektur microservices SiCure (Sistem Information Procurement). Fokus pengujian adalah memvalidasi bahwa sistem mampu menangani kegagalan Auth Service tanpa menyebabkan seluruh layanan procurement ikut terganggu.

---

## 1. Mekanisme Pertahanan Sistem

SiCure mengimplementasikan tiga mekanisme ketahanan yang bekerja secara berlapis pada `auth_client.py` di Procurement Service:

### 1.1 Retry dengan Exponential Backoff

Ketika Auth Service tidak merespons, Procurement Service tidak langsung menyerah. Sistem akan mencoba kembali sebanyak maksimal 3 kali dengan jeda yang semakin panjang:

```
Percobaan 1 → gagal → tunggu 0.5 detik
Percobaan 2 → gagal → tunggu 1.0 detik  
Percobaan 3 → gagal → kembalikan error 503
```

Tidak semua error layak untuk di-retry. Berikut aturannya:

| Jenis Error | Di-retry? | Penjelasan |
|-------------|-----------|------------|
| `ConnectError` | ✅ Ya | Service mungkin sedang proses restart |
| `TimeoutException` | ✅ Ya | Bisa jadi gangguan jaringan sementara |
| HTTP `500`, `502`, `503`, `504` | ✅ Ya | Error sisi server yang bersifat sementara |
| HTTP `401 Unauthorized` | ❌ Tidak | Token memang tidak valid, retry tidak akan membantu |
| HTTP `400 Bad Request` | ❌ Tidak | Data request salah, hasilnya akan tetap sama |

### 1.2 Circuit Breaker

Jika kegagalan terus berulang, Circuit Breaker akan "memutus arus" agar Procurement Service tidak terus-menerus menunggu Auth Service yang sudah pasti bermasalah.

| State | Kondisi | Perilaku Sistem |
|-------|---------|----------------|
| `CLOSED` | Normal | Semua request diteruskan ke Auth Service |
| `OPEN` | Setelah 5 kegagalan beruntun | Request langsung ditolak (fail fast <100ms) |
| `HALF_OPEN` | Setelah cooldown 30 detik | Satu request percobaan dikirim untuk mengecek pemulihan |

Alur perpindahan state:

```
CLOSED ──(5 kegagalan)──► OPEN ──(30 detik)──► HALF_OPEN
                                                    │
                                          ┌─────────┴─────────┐
                                    (berhasil)           (gagal lagi)
                                          │                    │
                                        CLOSED              OPEN
```

### 1.3 Graceful Degradation

Saat Auth Service tidak tersedia, sistem tidak langsung mati total. Endpoint publik yang tidak memerlukan autentikasi tetap dapat diakses, sementara endpoint yang memerlukan login akan memberikan respons error yang informatif.

---

## 2. Persiapan Sebelum Pengujian

Pastikan seluruh container microservices sudah berjalan:

```bash
# Jalankan semua service
docker compose up -d --build

# Verifikasi status container
docker compose ps
# Seluruh service harus berstatus: Up atau healthy
```

Lakukan pengecekan awal pada endpoint kesehatan masing-masing service:

```bash
# Gateway
curl -s http://localhost/health | python3 -m json.tool

# Auth Service
curl -s http://localhost/auth/health | python3 -m json.tool

# Procurement Service
curl -s http://localhost/procurement/health | python3 -m json.tool
```

---

## 3. Skenario Pengujian

### Skenario A — Pengujian Mekanisme Retry

**Tujuan pengujian:**
Memverifikasi bahwa Procurement Service melakukan percobaan ulang secara otomatis ketika Auth Service tidak dapat dihubungi, sebelum akhirnya mengembalikan respons error kepada pengguna.

**Langkah pengujian:**

```bash
# Langkah 1: Hentikan Auth Service
docker compose stop auth-service

# Langkah 2: Kirim request ke endpoint procurement yang memerlukan autentikasi
curl -i -X GET http://localhost/procurement/requisitions \
  -H "Authorization: Bearer test-token-sicure"

# Langkah 3: Pantau log Procurement Service untuk melihat percobaan retry
docker compose logs --tail=20 procurement-service
```

**Hasil yang diharapkan:**

- Sistem melakukan 3 kali percobaan dengan total waktu tunggu sekitar 3.5 detik
- Respons akhir: HTTP `503` dengan body:
  ```json
  {"detail": "Auth Service unavailable. Please try again later."}
  ```
- Log Procurement Service menampilkan jejak percobaan:
  ```
  Cannot connect to Auth Service (attempt 1/3)
  Retrying in 0.5s...
  Cannot connect to Auth Service (attempt 2/3)
  Retrying in 1.0s...
  Cannot connect to Auth Service (attempt 3/3)
  Auth Service unreachable after 3 attempts
  ```

**Status Pengujian:**

> ⚠️ **Pending** — akan diperbarui setelah implementasi microservices selesai. tanya ke muclis

---

### Skenario B — Pengujian Circuit Breaker (Fail Fast)

**Tujuan pengujian:**
Memverifikasi bahwa setelah sejumlah kegagalan beruntun mencapai batas threshold, Circuit Breaker beralih ke state `OPEN` dan mulai menolak request secara instan tanpa menunggu timeout.

**Langkah pengujian:**

```bash
# Langkah 1: Pastikan Auth Service masih dalam kondisi mati

# Langkah 2: Kirim 7 request berturut-turut dan catat waktu respons
for i in {1..7}; do
  printf "Request ke-%d: " $i
  curl -s -o /dev/null \
    -w "HTTP %{http_code} | Durasi: %{time_total}s\n" \
    -H "Authorization: Bearer test-token-sicure" \
    http://localhost/procurement/requisitions
done

# Langkah 3: Periksa state Circuit Breaker melalui health endpoint
curl -s http://localhost/procurement/health | python3 -m json.tool

# Langkah 4: Ukur durasi respons saat Circuit Breaker OPEN
time curl -s -o /dev/null \
  -H "Authorization: Bearer test-token-sicure" \
  http://localhost/procurement/requisitions
```

**Hasil yang diharapkan:**

- Request ke-1 hingga ke-5: respons lambat (~3.5 detik per request karena menunggu retry)
- Setelah kegagalan ke-5: state Circuit Breaker berubah dari `CLOSED` → `OPEN`
- Request ke-6 dan ke-7: respons sangat cepat (<100ms) dengan HTTP `503`:
  ```json
  {"detail": "Auth Service circuit breaker OPEN. Try again later."}
  ```
- Health endpoint menampilkan `"status": "degraded"` dan `"state": "OPEN"`

**Status Pengujian:**

> ⚠️ **Pending** — akan diperbarui setelah implementasi microservices selesai.

---

### Skenario C — Pengujian Pemulihan Otomatis

**Tujuan pengujian:**
Memverifikasi bahwa sistem dapat pulih secara otomatis setelah Auth Service kembali beroperasi, tanpa perlu melakukan restart manual pada service lain.

**Langkah pengujian:**

```bash
# Langkah 1: Nyalakan kembali Auth Service
docker compose start auth-service

# Langkah 2: Tunggu hingga periode cooldown selesai (30 detik)
echo "Menunggu cooldown 30 detik..."
sleep 35

# Langkah 3: Ambil token autentikasi yang valid
TOKEN=$(curl -s -X POST http://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sicure.id","password":"sicure2024"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'TOKEN_NOT_FOUND'))")

echo "Token diperoleh: ${TOKEN:0:30}..."

# Langkah 4: Akses endpoint procurement dengan token valid
curl -i -X GET http://localhost/procurement/requisitions \
  -H "Authorization: Bearer $TOKEN"

# Langkah 5: Verifikasi state Circuit Breaker sudah kembali normal
curl -s http://localhost/procurement/health | python3 -m json.tool
```

**Hasil yang diharapkan:**

- Request pertama setelah cooldown memicu transisi `OPEN` → `HALF_OPEN`
- Jika request berhasil, state langsung berubah menjadi `CLOSED`
- Respons endpoint procurement kembali normal dengan HTTP `200`
- Health endpoint kembali menampilkan `"status": "healthy"`
- Log Procurement Service: `Test berhasil! State: HALF_OPEN → CLOSED`

**Status Pengujian:**

> ⚠️ **Pending** — akan diperbarui setelah implementasi microservices selesai.

---

### Skenario D — Pengujian Graceful Degradation

**Tujuan pengujian:**
Memverifikasi bahwa sistem tetap dapat melayani sebagian fungsionalitas meskipun Auth Service sedang tidak tersedia, sehingga tidak semua pengguna terdampak.

**Langkah pengujian:**

```bash
# Langkah 1: Hentikan Auth Service
docker compose stop auth-service

# Langkah 2: Uji endpoint yang tidak memerlukan autentikasi
echo "=== Endpoint Publik (harus tetap bisa diakses) ==="
curl -i -X GET http://localhost/health
curl -i -X GET http://localhost/auth/health

# Langkah 3: Uji endpoint yang memerlukan autentikasi
echo "=== Endpoint Privat (harus ditolak) ==="
curl -i -X POST http://localhost/procurement/requisitions \
  -H "Authorization: Bearer test-token-sicure" \
  -H "Content-Type: application/json" \
  -d '{"item_name":"Laptop Dell","quantity":3,"reason":"Kebutuhan tim IT"}'

curl -i -X GET http://localhost/procurement/purchase-orders \
  -H "Authorization: Bearer test-token-sicure"
```

**Hasil yang diharapkan:**

- Endpoint publik (health check, gateway) tetap merespons dengan HTTP `200`
- Endpoint yang memerlukan login merespons dengan HTTP `503`
- Sistem tidak crash total — hanya fitur yang bergantung pada autentikasi yang tidak berfungsi

**Status Pengujian:**

> ⚠️ **Pending** — akan diperbarui setelah implementasi microservices selesai.

---

## 4. Struktur Respons Health Check

Endpoint `GET /procurement/health` mengembalikan informasi lengkap mengenai status layanan dan dependensinya:

```json
{
  "status": "healthy",
  "service": "procurement-service",
  "version": "2.0.0",
  "dependencies": {
    "auth-service": {
      "name": "auth-service",
      "state": "CLOSED",
      "failure_count": 0,
      "failure_threshold": 5,
      "total_rejected": 0,
      "cooldown_seconds": 30
    },
    "database": {
      "status": "connected"
    }
  }
}
```

Panduan membaca nilai `status`:

| Nilai Status | Kondisi Sistem | Tindakan |
|-------------|----------------|----------|
| `healthy` | Semua dependency normal, Circuit Breaker `CLOSED` | Tidak perlu tindakan |
| `degraded` | Auth Service bermasalah, Circuit Breaker `OPEN`/`HALF_OPEN` | Monitor dan tunggu pemulihan otomatis |
| `unhealthy` | Database tidak dapat diakses | Segera periksa koneksi database |

---

## 5. Ringkasan Hasil Pengujian

| Skenario | Fokus Pengujian | Target | Status |
|----------|----------------|--------|--------|
| A | Retry Logic | 3x retry dengan backoff, lalu HTTP 503 | ⚠️ Pending |
| B | Circuit Breaker Fast-Fail | Fail <100ms setelah 5 kegagalan | ⚠️ Pending |
| C | Pemulihan Otomatis | HALF_OPEN → CLOSED setelah Auth pulih | ⚠️ Pending |
| D | Graceful Degradation | Endpoint publik tetap HTTP 200 | ⚠️ Pending |

> ⚠️ **SESUAIKAN:** Perbarui kolom Status menjadi `✅ PASSED` atau `❌ FAILED` beserta catatan hasil aktual setelah pengujian dilakukan bersama tim.

---

## 6. Kesimpulan

Dokumen ini menjadi acuan pengujian ketahanan sistem microservices SiCure. Dengan menerapkan mekanisme Retry, Circuit Breaker, dan Graceful Degradation secara berlapis, sistem dirancang untuk tetap beroperasi meskipun terjadi gangguan pada Auth Service. Hal ini mencegah terjadinya cascading failure yang dapat melumpuhkan seluruh layanan procurement.

> ⚠️ **SESUAIKAN:** Perbarui kesimpulan ini dengan hasil aktual setelah seluruh skenario pengujian selesai dilakukan dan dikonfirmasi bersama tim.