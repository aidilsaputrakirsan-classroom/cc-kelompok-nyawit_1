# Docker Architecture — SICURE App

> ⚠️ **Catatan:** dokumen ini berisi catatan eksplorasi awal dan beberapa nilai
> sudah tidak sesuai dengan kode terbaru (mis. port, kredensial contoh). Untuk
> arsitektur **aktual** yang berjalan saat ini, lihat
> [system-architecture.md](system-architecture.md).

## Overview

Aplikasi SICURE dibangun menggunakan arsitektur berbasis container dengan tiga layanan utama, yaitu frontend, backend, dan database. Ketiga layanan tersebut dijalankan secara terpisah namun saling terhubung melalui satu Docker network.

---

## Container Details

### Frontend (React)

Frontend berperan sebagai antarmuka pengguna. Aplikasi ini berkomunikasi dengan backend melalui HTTP untuk mengambil dan mengirim data.

### Backend (FastAPI)

Backend berfungsi sebagai pengelola logika aplikasi dan penyedia API. Selain itu, backend juga bertugas untuk mengakses dan mengolah data dari database.

### Database (PostgreSQL)

Database digunakan untuk menyimpan seluruh data aplikasi. Data disimpan secara persisten menggunakan Docker volume.

---

## Ports

* Frontend: 3000
* Backend: 8000
* Database: 5432

---

## Network

Seluruh container terhubung dalam satu Docker network bernama:

`sicure-network`

Dengan konfigurasi ini, setiap service dapat saling berkomunikasi menggunakan nama container.

Relasi komunikasi:

* frontend mengakses backend
* backend mengakses database

---

## Volumes

* `sicure-pgdata` digunakan untuk menjaga data PostgreSQL tetap tersimpan meskipun container dihentikan.

---

## Environment Variables

### Backend

```id="o7n3x1"
DATABASE_URL=postgresql://postgres:adamdi@db:5432/sicure
```

### Database

```id="q2o9bq"
POSTGRES_USER=postgres
POSTGRES_PASSWORD=adamdi
POSTGRES_DB=sicure
```

---

## Architecture Diagram

```mermaid id="qk8z3n"
graph TD
    User --> Frontend[Frontend React Container]
    Frontend --> Backend[Backend FastAPI Container]
    Backend --> Database[(PostgreSQL Container)]
    Backend --> Network[(Docker Network)]
    Frontend --> Network
    Database --> Network
```

---

## Current Architecture (Single Container)

Pada tahap awal, aplikasi hanya dijalankan menggunakan satu container backend.

### Ports

* Backend: 8000

### Network

Backend terhubung ke Docker network `sicure-network`.

### Volumes

Belum menggunakan volume.

### Environment Variables

```id="b8f1yn"
DATABASE_URL=postgresql://postgres:adamdi@localhost:5432/sicure
```

### Diagram

```mermaid id="1txzq4"
graph TD
    User --> Backend[Backend FastAPI Container]
    Backend --> Network[(Docker Network: sicure-network)]
```

---

## Proposed Architecture (3-Container)

Pada pengembangan selanjutnya, sistem menggunakan tiga container yang dipisahkan berdasarkan fungsinya, yaitu frontend, backend, dan database.

### Ports

* Frontend: 3000
* Backend: 8000
* Database: 5432

### Network

Semua container berada dalam network yang sama, yaitu `sicure-network`, sehingga komunikasi antar layanan dapat berjalan dengan baik.

### Volumes

* `sicure-pgdata` digunakan untuk menyimpan data database secara persisten.

### Environment Variables

#### Backend

```id="9u6ycb"
DATABASE_URL=postgresql://postgres:adamdi@db:5432/sicure
```

#### Database

```id="6bptq2"
POSTGRES_USER=postgres
POSTGRES_PASSWORD=adamdi
POSTGRES_DB=sicure
```

### Architecture Diagram (3-Container)

```mermaid id="1p2x7c"
graph TD
    User((User))

    Frontend[Frontend React Container]
    Backend[Backend FastAPI Container]
    Database[(PostgreSQL Container)]
    Network[(Docker Network)]

    User --> Frontend
    Frontend --> Backend
    Backend --> Database

    Frontend --> Network
    Backend --> Network
    Database --> Network
```
