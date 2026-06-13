# System Architecture — SiCure

Dokumen ini menjelaskan arsitektur **aktual** SiCure yang berjalan saat ini:
aplikasi **monolith** (backend FastAPI + frontend React + PostgreSQL) yang
di-deploy ke Railway. Untuk catatan eksperimen microservices yang pernah
dilakukan, lihat [Release Notes](../release-notes.md).

> Stack: FastAPI + SQLAlchemy 2.0 (async) · React 19 + Vite · PostgreSQL 16 ·
> Docker · Railway (PaaS) · GitHub Actions (CI).

---

## 1. Deployment Architecture (Railway)

Satu Railway project berisi tiga service. Frontend dan backend masing-masing
punya domain publik; frontend memanggil backend langsung lewat `VITE_API_BASE_URL`
yang di-*bake* saat build.

```mermaid
flowchart TB
    user([User / Browser])

    subgraph railway["Railway Project: sicure"]
        fe["Frontend Service<br/>nginx + React bundle<br/>:$PORT"]
        be["Backend Service<br/>FastAPI + Uvicorn<br/>:$PORT"]
        db[("PostgreSQL<br/>managed service")]
    end

    user -->|"HTTPS<br/>sicure-app.up.railway.app"| fe
    user -->|"HTTPS (XHR/fetch)<br/>sicure-api.up.railway.app/api/v1"| be
    be -->|"asyncpg<br/>DATABASE_URL"| db

    gh["GitHub repo (main)"] -. "push/merge → auto-deploy" .-> fe
    gh -. "push/merge → auto-deploy" .-> be
```

Karakteristik:
- **Auto-deploy**: setiap merge ke `main`, Railway rebuild & redeploy kedua service.
- **Migrasi otomatis**: container backend menjalankan `alembic upgrade head` saat start.
- **Persistensi**: data tersimpan di PostgreSQL managed (bukan di filesystem container).

---

## 2. Request Flow (User → Gateway → Service → DB)

```mermaid
sequenceDiagram
    participant U as User (React SPA)
    participant API as FastAPI (Backend)
    participant MW as Middleware<br/>(CORS, Correlation ID, Logging)
    participant DEP as Auth Dependency<br/>(get_current_user)
    participant R as Router/Service
    participant DB as PostgreSQL

    U->>API: HTTP request + JWT (Authorization: Bearer)
    API->>MW: assign/echo X-Correlation-ID, log request.start
    MW->>DEP: decode JWT, cek blacklist, ambil user
    alt token invalid / tidak ada
        DEP-->>U: 401 Unauthorized
    else token valid
        DEP->>R: user terautentikasi
        R->>DB: query (async SQLAlchemy)
        DB-->>R: hasil
        R-->>MW: response
        MW-->>U: response + X-Correlation-ID, log request.end (status, durasi)
    end
```

Poin penting:
- Setiap request mendapat **correlation ID** (di-generate atau diambil dari header
  `X-Correlation-ID`/`X-Request-ID`) yang muncul di seluruh log request tersebut.
- Endpoint terproteksi memakai dependency `get_current_user` / `require_role`,
  sehingga akses tanpa token valid ditolak `401`.

---

## 3. Component / Module View (Backend)

```mermaid
flowchart LR
    subgraph app["backend/app"]
        main["main.py<br/>app + middleware + /health"]
        subgraph routers["routers/"]
            auth_r["auth"]
            req_r["requisitions (+admin)"]
            po_r["purchase_orders"]
            grn_r["grn (+admin)"]
        end
        core["core/<br/>config · security · deps · logging_config"]
        services["services/<br/>vendor_quote_rules"]
        models["models/ (SQLAlchemy)"]
        schemas["schemas/ (Pydantic)"]
        db["db/<br/>async engine + session"]
    end
    main --> routers
    routers --> core
    routers --> services
    routers --> schemas
    routers --> models
    models --> db
    core --> db
```

---

## 4. Procurement State Machine

Status sebuah Purchase Requisition (PR) selama siklus procurement:

```mermaid
stateDiagram-v2
    [*] --> SUBMITTED: Requester buat PR + vendor quotes
    SUBMITTED --> REJECTED: Admin REJECT
    SUBMITTED --> PO_ISSUED: Admin APPROVE (PO terbit)
    REJECTED --> SUBMITTED: Requester revisi & ajukan ulang
    PO_ISSUED --> DOC_SUBMITTED: Requester upload GRN (invoice + foto)
    DOC_SUBMITTED --> PO_ISSUED: Admin RETURN (perbaiki dokumen)
    DOC_SUBMITTED --> VERIFIED: Admin verifikasi
    VERIFIED --> CLOSED: Admin tutup procurement
    CLOSED --> [*]
```

---

## 5. CI/CD Pipeline

```mermaid
flowchart LR
    push["push / PR ke main"] --> tb["test-backend<br/>pytest (unit + integration)"]
    push --> tf["test-frontend<br/>vitest + build"]
    tb --> bd["build-docker<br/>backend + frontend image"]
    tf --> bd
    bd --> vd["verify-deploy*<br/>health check production URL"]
    note["* hanya pada push ke main;<br/>deploy aktual oleh Railway auto-deploy"]
```

Detail langkah ada di [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
dan panduan deploy di [railway-deployment.md](../railway-deployment.md).
