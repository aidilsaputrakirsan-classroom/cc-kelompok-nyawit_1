# Makefile Usage — SiCure Microservices

Makefile ini mempermudah pengelolaan Docker Compose untuk arsitektur microservices.

## Quick Start

```bash
# Lihat semua commands
make help

# Start semua services
make up

# Lihat logs semua services
make logs

# Stop semua services
make down
```

## Commands Lengkap

### Main Commands

| Command | Deskripsi |
|---------|-----------|
| `make up` | Start semua services (build jika perlu) |
| `make down` | Stop dan hapus semua containers |
| `make restart` | Restart semua services |
| `make logs` | Stream logs dari semua services (Ctrl+C untuk exit) |

### Monitoring

| Command | Deskripsi |
|---------|-----------|
| `make ps` | Lihat status semua containers |
| `make health` | Cek health endpoint semua services |

### Development

| Command | Deskripsi |
|---------|-----------|
| `make build` | Rebuild semua images dari scratch |
| `make seed` | Jalankan seeder Auth Service (buat user demo) |
| `make clean` | Stop + hapus containers & volumes (⚠️ data hilang) |

### Individual Service Logs

| Command | Deskripsi |
|---------|-----------|
| `make logs-auth` | Logs Auth Service saja |
| `make logs-proc` | Logs Procurement Service saja |
| `make logs-gateway` | Logs Gateway saja |
| `make logs-frontend` | Logs Frontend saja |
| `make logs-db` | Logs kedua database |

### Shell Access

| Command | Deskripsi |
|---------|-----------|
| `make shell-auth` | Buka shell di container Auth Service |
| `make shell-proc` | Buka shell di container Procurement Service |
| `make shell-gateway` | Buka shell di container Gateway |

### Testing

| Command | Deskripsi |
|---------|-----------|
| `make test` | Smoke test (cek health endpoints) |

## Typical Workflow

### Development

```bash
# 1. Start semua services
make up

# 2. Cek status
make ps

# 3. Seed database dengan user demo
make seed

# 4. Lihat logs real-time
make logs
```

### Debugging

```bash
# Lihat logs service tertentu
make logs-auth
make logs-proc

# Masuk ke container untuk debug
make shell-auth
make shell-proc

# Cek health endpoint
make health
```

### Restart After Changes

```bash
# Rebuild dan restart semua
make build
make restart

# Atau langsung
make down && make up
```

### Cleanup

```bash
# Stop saja (data tetap ada)
make down

# Stop + hapus data (fresh start)
make clean
```

## Environment

Makefile menggunakan file compose: `docker-compose.microservices.yml`

Untuk custom compose file, edit variabel `COMPOSE_FILE` di Makefile.

## Requirements

- `make` (GNU Make)
- `docker` & `docker compose`
- `curl` (untuk health checks)
- `python3` (untuk JSON formatting di health check)

## Tugas Modul 12

Makefile ini memenuhi requirement:
> Lead DevOps: Tambah health checks di Docker Compose. Gateway hanya start setelah semua service healthy. Buat `Makefile` target: `up`, `down`, `logs`, `restart`.

✅ Targets wajib: `up`, `down`, `logs`, `restart`  
✅ Bonus: `build`, `seed`, `clean`, `health`, `ps`, individual logs, shell access
