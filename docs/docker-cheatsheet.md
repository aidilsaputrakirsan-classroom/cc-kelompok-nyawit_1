# Docker Cheatsheet

Ringkasan perintah Docker yang sering dipakai, disertai contoh **khusus proyek cc-kelompok-nyawit_1** (backend FastAPI di `backend/`, port **8000**).

> **Catatan proyek:** Hanya folder `backend/` yang punya `Dockerfile`. Frontend (`frontend/`) umumnya dijalankan dengan `npm run dev` di host, dengan `VITE_API_URL=http://localhost:8000` mengarah ke API yang berjalan di container (mapping port `-p 8000:8000`).

---

## Build — buat image dari Dockerfile

| Perintah | Keterangan singkat |
|----------|-------------------|
| `docker build -t nama:image .` | Build dari `Dockerfile` di direktori saat ini |
| `docker build -t nama:image -f path/Dockerfile .` | Pakai Dockerfile di path tertentu |

**Contoh proyek ini (dari root repo):**

```bash
cd cc-kelompok-nyawit_1
docker build -t sicure-backend:latest ./backend
```

**Contoh dari dalam folder `backend`:**

```bash
cd backend
docker build -t sicure-backend:latest .
```

---

## Run — jalankan container

| Perintah | Keterangan singkat |
|----------|-------------------|
| `docker run IMAGE` | Satu proses foreground (terminal tertahan) |
| `docker run -d IMAGE` | Detach (background) |
| `docker run -p HOST:CONTAINER` | Publikasikan port (mis. `-p 8000:8000`) |
| `docker run --name NAMA` | Beri nama container agar mudah di-`stop`/`rm` |
| `docker run --rm IMAGE` | Hapus container otomatis setelah berhenti |

**Contoh proyek ini — API bisa diakses di `http://localhost:8000`:**

```bash
docker run --name sicure-api -p 8000:8000 sicure-backend:latest
```

**Background + hapus otomatis setelah stop:**

```bash
docker run -d --rm --name sicure-api -p 8000:8000 sicure-backend:latest
```

> Backend membaca konfigurasi database lewat variabel lingkungan (lihat `.env.example` di `backend/`). File `.env` **tidak** ikut ke image (ada di `.dockerignore`). Untuk produksi/dev dengan DB, gunakan `--env-file` atau `-e KEY=VALUE` saat `docker run`, atau mount file env yang aman.

**Contoh dengan file env (setelah Anda siapkan `backend/.env.docker` atau salinan yang aman):**

```bash
docker run -d --name sicure-api -p 8000:8000 --env-file backend/.env sicure-backend:latest
```

---

## ps — daftar container & status

| Perintah | Keterangan |
|----------|------------|
| `docker ps` | Container yang sedang berjalan |
| `docker ps -a` | Semua container (termasuk berhenti) |
| `docker ps -q` | Hanya ID (berguna untuk skrip) |

**Contoh:**

```bash
docker ps
docker ps -a --filter "name=sicure-api"
```

---

## logs — lihat log container

| Perintah | Keterangan |
|----------|------------|
| `docker logs NAMA_ATAU_ID` | Log stdout/stderr |
| `docker logs -f NAMA` | Follow (seperti `tail -f`) |
| `docker logs --tail 100 NAMA` | 100 baris terakhir |

**Contoh proyek ini:**

```bash
docker logs -f sicure-api
```

---

## exec — masuk ke shell atau jalankan perintah di dalam container

| Perintah | Keterangan |
|----------|------------|
| `docker exec -it NAMA sh` | Shell interaktif (image slim biasanya `sh`) |
| `docker exec NAMA perintah` | Satu perintah sekali jalan |

**Contoh — cek health dari dalam jaringan container (opsional):**

```bash
docker exec sicure-api curl -s http://localhost:8000/health
```

**Contoh — shell di dalam container:**

```bash
docker exec -it sicure-api sh
```

---

## stop — hentikan container

| Perintah | Keterangan |
|----------|------------|
| `docker stop NAMA_ATAU_ID` | Stop anggun (SIGTERM lalu SIGKILL) |
| `docker stop $(docker ps -q)` | Stop semua yang jalan (hati-hati di mesin bersama) |

**Contoh:**

```bash
docker stop sicure-api
```

---

## rm — hapus container

| Perintah | Keterangan |
|----------|------------|
| `docker rm NAMA_ATAU_ID` | Hapus container yang sudah stop |
| `docker rm -f NAMA` | Paksa stop + hapus |

**Contoh:**

```bash
docker rm sicure-api
docker rm -f sicure-api
```

---

## pull — unduh image dari registry

| Perintah | Keterangan |
|----------|------------|
| `docker pull nginx:alpine` | Unduh tag tertentu dari Docker Hub |
| `docker pull ghcr.io/org/image:tag` | Contoh GitHub Container Registry |

**Contoh (umum, bukan image proyek ini):**

```bash
docker pull postgres:16-alpine
```

Image backend proyek ini biasanya **dibangun lokal** dengan `docker build`; `pull` relevan jika Anda menerbitkan image ke registry tim.

---

## push — unggah image ke registry

Langkah singkat: login → tag → push.

```bash
docker login
docker tag sicure-backend:latest REGISTRY/USER/sicure-backend:1.0.0
docker push REGISTRY/USER/sicure-backend:1.0.0
```

Ganti `REGISTRY/USER` dengan Docker Hub, GHCR, atau registry internal tim Anda.

---

## Perintah tambahan yang berguna

| Perintah | Keterangan |
|----------|------------|
| `docker images` | Daftar image lokal |
| `docker rmi IMAGE` | Hapus image |
| `docker system prune` | Bersihkan cache/container/network tidak terpakai (hati-hati) |
| `docker inspect NAMA` | Metadata container (IP, env, mount, dll.) |

---

## Alur singkat dev proyek ini

1. **Build image backend:** `docker build -t sicure-backend:latest ./backend`
2. **Jalankan API:** `docker run -d --name sicure-api -p 8000:8000 --env-file backend/.env sicure-backend:latest`  
   *(sesuaikan env agar `DATABASE_URL` mengarah ke PostgreSQL yang bisa dijangkau dari host/container — di Windows/Mac sering `host.docker.internal` untuk DB di host.)*
3. **Cek API:** buka `http://localhost:8000/docs` (Swagger) atau `http://localhost:8000/health`
4. **Frontend di host:** `cd frontend && npm run dev` dengan `VITE_API_URL=http://localhost:8000`

---

## Referensi cepat satu baris

```text
build   → docker build -t sicure-backend:latest ./backend
run     → docker run -d --name sicure-api -p 8000:8000 sicure-backend:latest
ps      → docker ps
logs    → docker logs -f sicure-api
exec    → docker exec -it sicure-api sh
stop    → docker stop sicure-api
rm      → docker rm sicure-api
pull    → docker pull postgres:16-alpine
push    → docker tag … && docker push …
```
