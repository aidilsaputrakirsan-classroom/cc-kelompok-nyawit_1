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

---

## 5. Microservices Decomposition (Future Architecture)

Saat ini SiCure menggunakan **modular monolith** architecture — semua module dalam satu codebase tapi dengan clear separation of concerns. Jika sistem perlu scale atau tim berkembang, berikut adalah decomposition ke microservices yang direkomendasikan:

### Proposed Service Boundaries

```mermaid
graph TB
    subgraph "Current: Modular Monolith"
        A[Auth Service Module]
        B[Requisition Service Module]
        C[PO Service Module]
        D[GRN Service Module]
        E[Notification Service Module]
    end
    
    subgraph "Future: Microservices"
        F[Auth Service<br/>JWT + User Management]
        G[PR Service<br/>Purchase Requisitions]
        H[PO Service<br/>Purchase Orders]
        I[GRN Service<br/>Goods Receipt]
        J[Notification Service<br/>Email + Alerts]
    end
    
    A -."Refactor into".-> F
    B -."Refactor into".-> G
    C -."Refactor into".-> H
    D -."Refactor into".-> I
    E -."Refactor into".-> J
```

### Service Decomposition Rationale

| Service | Responsibility | Database Schema | Communication |
|---------|---------------|-----------------|---------------|
| **Auth Service** | User registration, login, JWT issuance, token blacklist | `users`, `token_blacklist` | REST API for token validation |
| **PR Service** | Create/edit PR, vendor quote management, category filtering | `requisitions`, `line_items`, `vendor_quotes` | Events: `pr.submitted`, `pr.approved` |
| **PO Service** | Auto-generate PO from approved PR, vendor assignment | `purchase_orders` | Consumes: `pr.approved` event |
| **GRN Service** | Document upload, verification workflow, status tracking | `grn_records`, `grn_documents` | Consumes: `po.issued` event |
| **Notification Service** | Email notifications, status change alerts | `notifications`, `email_templates` | Consumes all domain events |

### Inter-Service Communication Patterns

**1. Synchronous (REST/gRPC)**
- Auth service expose endpoint `/validate-token` untuk service lain verify JWT
- PR service call Auth service untuk get user details by ID

**2. Asynchronous (Event-Driven via Message Queue)**
```mermaid
sequenceDiagram
    participant PR as PR Service
    participant MQ as Message Queue<br/>(RabbitMQ/Redis)
    participant PO as PO Service
    participant NOTIF as Notification Service
    
    PR->>MQ: Publish event: pr.approved {pr_id, vendor_id}
    MQ->>PO: Deliver event
    PO->>PO: Generate PO record
    PO->>MQ: Publish event: po.issued {po_id, pr_id}
    MQ->>NOTIF: Deliver event
    NOTIF->>NOTIF: Send email to requester
```

**3. Shared Database vs Database-per-Service**
- **Current:** Single PostgreSQL database dengan shared schema
- **Future:** Each service has own database schema, communicate via APIs/events
- **Challenge:** Distributed transactions (use Saga pattern untuk maintain consistency)

### Why We Chose Monolith First

1. **Team Size:** 5 orang → coordination overhead microservices tidak worth it
2. **Complexity:** Business logic belum cukup complex untuk justify service boundaries
3. **Deployment Simplicity:** Satu deployment unit lebih mudah manage di Railway
4. **Performance:** No network latency antara modules (in-process calls vs HTTP)
5. **Development Speed:** Faster iteration tanpa concern service versioning

### When to Migrate to Microservices

Migration justified ketika:
- ✅ Tim > 10 developers dengan multiple squads
- ✅ Different scaling requirements (misal: GRN upload butuh more resources)
- ✅ Independent deployment needs (tim frontend butuh release lebih sering)
- ✅ Technology diversity (misal: notification service better dengan Node.js)
- ✅ Fault isolation critical (satu service down tidak affect others)

### Current Modular Design Enables Future Migration

Codebase saat ini sudah structured untuk memudahkan future extraction:
- **Clear module boundaries:** `app/routers/`, `app/models/`, `app/services/` per domain
- **Dependency injection:** Services tidak hard-depend pada implementation details
- **Event-driven patterns:** Status transitions bisa easily convert ke events
- **API-first design:** External contracts sudah well-defined via Pydantic schemas

Ini berarti migration path jelas: extract module → create separate service → replace in-process calls dengan HTTP/event communication.
