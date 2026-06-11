# Pengujian Ketahanan Sistem — SiCure

Dokumen ini mendefinisikan pendekatan pengujian **ketahanan sistem (reliability testing)** pada arsitektur microservices SiCure (System Information Procurement). Fokus pengujian adalah memvalidasi bahwa sistem mampu menangani kegagalan Auth Service menggunakan Retry, Circuit Breaker, dan Graceful Degradation tanpa menyebabkan seluruh layanan procurement ikut terganggu.

---

## 1. Mekanisme Pertahanan Sistem

SiCure mengimplementasikan tiga mekanisme ketahanan yang bekerja secara berlapis pada `deps.py` di Procurement Service:

### 1.1 Retry dengan Exponential Backoff

Ketika Auth Service tidak merespons, Procurement Service tidak langsung menyerah. Sistem akan mencoba kembali sebanyak maksimal 3 kali dengan jeda yang semakin panjang:

```
Percobaan 1 → gagal → tunggu 0.5 detik
Percobaan 2 → gagal → tunggu 1.0 detik  
Percobaan 3 → gagal → tunggu 2.0 detik
Setelah percobaan 3 gagal → kembalikan error 503
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

Saat Auth Service tidak tersedia, sistem tidak langsung mati total. 
- Endpoint publik seperti `/api/v1/requisitions/public` tetap dapat diakses tanpa token.
- Endpoint statistik `/api/v1/requisitions/stats` dapat diakses tanpa token dalam **degraded mode** (mengembalikan statistik global secara anonim dengan flag `"degraded": true`).
- Endpoint yang memerlukan verifikasi token wajib (seperti pembuatan/pengubahan PR) akan mendeteksi circuit breaker OPEN atau Auth Service down dan mengembalikan status HTTP `503 Service Unavailable` secara instan (*fast fail*).

---

## 2. Persiapan Sebelum Pengujian

Pastikan seluruh container microservices sudah berjalan:

```bash
# Jalankan semua service
docker compose -f docker-compose.microservices.yml up -d --build

# Verifikasi status container
docker compose -f docker-compose.microservices.yml ps
# Seluruh service harus berstatus: Up atau healthy
```

Lakukan pengecekan awal pada endpoint kesehatan masing-masing service:

```bash
# Gateway
curl -s http://localhost/health | python3 -m json.tool

# Auth Service
curl -s http://localhost/api/v1/auth/health | python3 -m json.tool

# Procurement Service (Aggregated health check via docker exec)
docker exec sicure-procurement-service curl -s http://localhost:8002/health | python3 -m json.tool
```

---

## 3. Skenario Pengujian

### Skenario A — Pengujian Mekanisme Retry

**Tujuan pengujian:**
Memverifikasi bahwa Procurement Service melakukan percobaan ulang secara otomatis ketika Auth Service tidak dapat dihubungi, sebelum akhirnya mengembalikan respons error kepada pengguna.

**Langkah pengujian:**

```bash
# Langkah 1: Hentikan Auth Service
docker compose -f docker-compose.microservices.yml stop auth-service

# Langkah 2: Kirim request ke endpoint procurement yang memerlukan autentikasi
curl -i -X GET http://localhost/api/v1/requisitions/ \
  -H "Authorization: Bearer test-token-sicure"

# Langkah 3: Pantau log Procurement Service untuk melihat percobaan retry
docker compose -f docker-compose.microservices.yml logs --tail=20 procurement-service
```

**Hasil Aktual & Verifikasi:**
- Sistem melakukan 3 kali percobaan dengan total waktu jeda bertahap (0.5s, 1.0s, 2.0s).
- Respons akhir: HTTP `503 Service Unavailable` dengan body:
  ```json
  {"detail": "Auth Service tidak tersedia saat ini."}
  ```
- Log Procurement Service menampilkan jejak percobaan:
  ```
  Connection/Timeout error with Auth Service (attempt 1/3): ...
  Connection/Timeout error with Auth Service (attempt 2/3): ...
  Connection/Timeout error with Auth Service (attempt 3/3): ...
  ```

**Status Pengujian:** `✅ PASSED`

---

### Skenario B — Pengujian Circuit Breaker (Fail Fast)

**Tujuan pengujian:**
Memverifikasi bahwa setelah sejumlah kegagalan beruntun mencapai batas threshold (5 kali), Circuit Breaker beralih ke state `OPEN` dan mulai menolak request secara instan tanpa menunggu timeout.

**Langkah pengujian:**

```bash
# Langkah 1: Pastikan Auth Service masih dalam kondisi mati

# Langkah 2: Kirim 7 request berturut-turut dan catat waktu respons
for i in {1..7}; do
  printf "Request ke-%d: " $i
  curl -s -o /dev/null \
    -w "HTTP %{http_code} | Durasi: %{time_total}s\n" \
    -H "Authorization: Bearer test-token-sicure" \
    http://localhost/api/v1/requisitions/
done

# Langkah 3: Periksa state Circuit Breaker melalui health endpoint
docker exec sicure-procurement-service curl -s http://localhost:8002/health | python3 -m json.tool
```

**Hasil Aktual & Verifikasi:**
- Request ke-1 hingga ke-5: respons lambat (>3.5 detik per request karena menunggu retry).
- Setelah kegagalan ke-5: state Circuit Breaker berubah dari `CLOSED` → `OPEN`.
- Request ke-6 dan ke-7: respons sangat cepat (<100ms) dengan HTTP `503 Service Unavailable`:
  ```json
  {"detail": "Auth Service circuit breaker OPEN. Try again later."}
  ```
- Health endpoint menampilkan `"status": "degraded"` dan `"state": "OPEN"`.

**Status Pengujian:** `✅ PASSED`

---

### Skenario C — Pengujian Pemulihan Otomatis

**Tujuan pengujian:**
Memverifikasi bahwa sistem dapat pulih secara otomatis setelah Auth Service kembali beroperasi, tanpa perlu melakukan restart manual pada service lain.

**Langkah pengujian:**

```bash
# Langkah 1: Nyalakan kembali Auth Service
docker compose -f docker-compose.microservices.yml start auth-service

# Langkah 2: Tunggu hingga periode cooldown selesai (30 detik)
echo "Menunggu cooldown 30 detik..."
sleep 35

# Langkah 3: Ambil token autentikasi yang valid untuk user yang diseed
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"requester1@sicure.com","password":"requester1234"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('access_token', 'TOKEN_NOT_FOUND'))")

echo "Token diperoleh: ${TOKEN:0:30}..."

# Langkah 4: Akses endpoint procurement dengan token valid
curl -i -X GET http://localhost/api/v1/requisitions/ \
  -H "Authorization: Bearer $TOKEN"

# Langkah 5: Verifikasi state Circuit Breaker sudah kembali normal
docker exec sicure-procurement-service curl -s http://localhost:8002/health | python3 -m json.tool
```

**Hasil Aktual & Verifikasi:**
- Request pertama setelah cooldown memicu transisi `OPEN` → `HALF_OPEN`.
- Karena request tersebut berhasil menghubungi Auth Service dengan sukses, state langsung berubah menjadi `CLOSED`.
- Respons endpoint procurement kembali normal dengan HTTP `200 OK`.
- Health endpoint kembali menampilkan `"status": "healthy"` dan `"state": "CLOSED"`.

**Status Pengujian:** `✅ PASSED`

---

### Skenario D — Pengujian Graceful Degradation

**Tujuan pengujian:**
Memverifikasi bahwa sistem tetap dapat melayani sebagian fungsionalitas meskipun Auth Service sedang tidak tersedia, sehingga tidak semua pengguna terdampak secara total.

**Langkah pengujian:**

```bash
# Langkah 1: Hentikan Auth Service kembali
docker compose -f docker-compose.microservices.yml stop auth-service

# Langkah 2: Uji endpoint yang tidak memerlukan autentikasi (Public & Stats Degraded)
echo "=== Endpoint Publik Requisitions (harus tetap bisa diakses) ==="
curl -i -X GET http://localhost/api/v1/requisitions/public

echo "=== Endpoint Stats Requisitions (harus merespons dengan degraded: true) ==="
curl -i -X GET http://localhost/api/v1/requisitions/stats

# Langkah 3: Uji endpoint yang memerlukan autentikasi wajib
echo "=== Endpoint Privat Requisitions (harus ditolak) ==="
curl -i -X GET http://localhost/api/v1/requisitions/ \
  -H "Authorization: Bearer test-token-sicure"
```

**Hasil Aktual & Verifikasi:**
- Endpoint `/api/v1/requisitions/public` tetap merespons dengan HTTP `200 OK` dan menampilkan data.
- Endpoint `/api/v1/requisitions/stats` tetap merespons dengan HTTP `200 OK` dan menampilkan data statistik global, dengan flag `"degraded": true`.
- Endpoint privat `/api/v1/requisitions/` ditolak dengan HTTP `503 Service Unavailable` karena Auth Service mati.
- Sistem tidak crash total — hanya fitur yang bergantung penuh pada autentikasi yang tidak berfungsi sementara.

**Status Pengujian:** `✅ PASSED`

---

## 4. Struktur Respons Health Check

Endpoint `GET http://localhost:8002/health` (atau melalui docker exec) mengembalikan informasi lengkap mengenai status layanan dan dependensinya:

```json
{
    "status": "healthy",
    "service": "procurement-service",
    "version": "1.0.0",
    "checks": {
        "database": {
            "status": "healthy"
        },
        "circuit_breaker": {
            "status": "healthy",
            "name": "auth-service",
            "state": "CLOSED",
            "failure_count": 0,
            "failure_threshold": 5,
            "total_rejected": 0,
            "cooldown_seconds": 30
        },
        "auth_service": {
            "status": "healthy"
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
| **A** | Retry Logic | 3x retry dengan backoff, lalu HTTP 503 | `✅ PASSED` |
| **B** | Circuit Breaker Fast-Fail | Fail <100ms setelah 5 kegagalan beruntun | `✅ PASSED` |
| **C** | Pemulihan Otomatis | HALF_OPEN → CLOSED setelah Auth pulih | `✅ PASSED` |
| **D** | Graceful Degradation | Endpoint publik & stats degraded tetap berjalan | `✅ PASSED` |

---

## 6. Kesimpulan

Mekanisme pertahanan berlapis (Retry, Circuit Breaker, dan Graceful Degradation) telah diimplementasikan dengan sukses pada Procurement Service. Pengujian ketahanan sistem membuktikan bahwa ketika Auth Service mengalami gangguan:
1. Sistem mencegah penumpukan request melalui strategi *fail fast* (Circuit Breaker OPEN).
2. Sistem meminimalisasi dampak bagi pengguna dengan membiarkan fitur publik dan data statistik global tetap dapat diakses (*degraded mode*).
3. Layanan secara otomatis pulih kembali (*self-healing*) ke kondisi normal (*CLOSED* state) sesaat setelah Auth Service sehat kembali tanpa memerlukan intervensi operasional manual.