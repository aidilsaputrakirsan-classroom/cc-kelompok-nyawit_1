# Reflection Paper — Muchlis Wahyu Saputra

- **NIM:** 10231054
- **Peran:** Lead Backend
- **Proyek:** SiCure — Sistem Informasi Procurement

## 1. Ringkasan Kontribusi
Sebagai Lead Backend, saya bertanggung jawab atas arsitektur dan implementasi seluruh API backend SiCure menggunakan FastAPI. Fokus utama saya adalah merancang model data yang efisien untuk alur procurement (PR → PO → GRN), mengimplementasikan sistem autentikasi JWT dengan token rotation dan blacklist untuk logout aman, serta membangun aturan bisnis kompleks untuk validasi vendor quotes (3-quotation rule). Saya juga menambahkan observability melalui structured logging JSON dengan correlation ID tracking untuk memudahkan debugging di production Railway.

## 2. Keputusan Teknis & Alasannya

### Mengapa FastAPI + SQLAlchemy Async?
Saya memilih **FastAPI** karena performance tinggi dan dokumentasi Swagger otomatis yang sangat membantu tim frontend memahami API tanpa perlu dokumentasi manual. Penggunaan **SQLAlchemy 2.0 async** dengan `asyncpg` memberikan throughput lebih baik dibanding sync ORM saat menangani banyak concurrent requests, terutama penting untuk aplikasi cloud yang harus scale horizontal. Trade-off-nya adalah learning curve lebih curam dan testing lebih kompleks (perlu `pytest-asyncio`), tapi ini worth it untuk performa jangka panjang.

### Mengapa JWT Access + Refresh Token dengan Blacklist?
Desain ini dipilih untuk **security best practice**. Access token berumur pendek (15 menit) membatasi damage jika token dicuri, sementara refresh token (7 hari) memungkinkan user tetap login tanpa re-authentication berulang. Token blacklist diperlukan untuk implementasi **logout yang benar** — tanpa blacklist, access token tetap valid sampai expired meskipun user sudah logout. Ini trade-off antara statelessness JWT (ideal) vs kebutuhan security praktis (stateful revocation).

### Mengapa Structured Logging JSON + Correlation ID?
Di production Railway, kita tidak bisa SSH ke container untuk debug. Dengan **JSON logs**, log bisa diparsing otomatis oleh monitoring tools. **Correlation ID** yang digenerate per request dan diteruskan ke semua log entry memungkinkan tracing end-to-end: dari request masuk → query database → response keluar. Saat ada error, cukup search correlation ID untuk melihat seluruh lifecycle request tersebut. Ini critical untuk debugging distributed system.

### Mengapa Envelope Response `{success, data, message}`?
Konsistensi response format memudahkan frontend handling. Daripada setiap endpoint punya struktur berbeda, semua response mengikuti pola yang sama. Field `success` boolean untuk quick check, `data` untuk payload, `message` untuk human-readable info. Error response juga konsisten dengan field `detail`. Ini mengurangi cognitive load developer frontend dan membuat error handling lebih predictable.

## 3. Kesulitan & Cara Mengatasi

### Masalah 1: File Upload dengan Validasi Vendor Quotes
Tantangan terbesar adalah endpoint `POST /requisitions/` yang menerima multipart form data dengan multiple file uploads (bukti survei vendor) sambil melakukan validasi kompleks: jumlah vendor minimal sesuai threshold nilai PR, satu vendor harus marked recommended, total harga dihitung otomatis. Awalnya saya coba handle semua di router, tapi kode jadi sangat panjang dan sulit di-test.

**Solusi:** Saya refactor dengan memisahkan concern:
- Router hanya handle HTTP layer (parse form, validate files)
- Service layer (`QuoteValidationService`) handle business logic
- Utility functions untuk file storage dan sanitization
- Integration test `test_integration_flow.py` memvalidasi entire flow end-to-end

Ini membuat kode lebih maintainable dan testable. Coverage naik dari 60% ke 95% setelah refactoring.

### Masalah 2: Alembic Migration Konflik di Tim
Saat tim bekerja paralel, sering terjadi migration conflict — dua orang create migration berbeda yang mengubah tabel sama. Awalnya kami resolve manual dengan merge, tapi ini error-prone.

**Solusi:** Kami establish workflow:
1. Selalu pull latest main sebelum create migration baru
2. Test migration up/down di local sebelum push
3. Untuk perubahan besar, koordinasi dulu di Discord
4. Gunakan `alembic downgrade base && alembic upgrade head` untuk verify clean migration

Workflow ini mengurangi conflict secara signifikan.

### Masalah 3: Testing Async Database Operations
Testing FastAPI async endpoints dengan SQLite in-memory tricky karena transaction isolation. Test yang bergantung pada data dari test sebelumnya sering fail karena data tidak commit atau session tidak di-flush.

**Solusi:** 
- Setup fixture `client` yang properly manage async session lifecycle
- Gunakan `db.flush()` setelah insert di test untuk make data visible
- Mark integration tests dengan `@pytest.mark.integration` agar bisa run selective
- Mock external dependencies (email service, file storage) untuk unit tests

Setelah setup conftest.py yang proper, test suite stabil dan fast (~12 detik untuk 45 tests).

## 4. Pelajaran yang Diambil

### Security First
Awalnya saya taruh auth middleware di akhir development. Ternyata ini salah besar banyak endpoint yang lupa di-protect, dan refactor jadi painful. Sekarang saya selalu start dengan: "Endpoint ini butuh auth? Role apa?" sebelum write code. Implement RBAC dari awal, bukan tambahkan nanti.

### Documentation is Code
Swagger docs otomatis dari FastAPI itu bagus, tapi tidak cukup. Saya belajar bahwa **API contract document** (`docs/api-contract.md`) yang menjelaskan business context, contoh request/response, dan edge cases jauh lebih valuable untuk kolaborasi tim. Frontend dev bisa work parallel tanpa wait backend selesai.

### Observability Bukan Optional
Dulu saya anggap logging itu "nice to have". Tapi saat deploy ke Railway dan ada bug, saya realize betapa pentingnya structured logging dengan correlation ID. Tanpa itu, debugging production seperti cari jarum di tumpukan jerami. Sekarang observability (logging, metrics, health checks) jadi prioritas sejak day one.

### Test Coverage > Feature Velocity
Awalnya saya skip tests untuk cepat deliver features. Tapi technical debt menumpuk setiap change breaking existing functionality tanpa ketahuan. Setelah enforce minimum 40% coverage (sekarang 95%), development justru lebih cepat karena confidence untuk refactor dan catch bugs early di CI pipeline.

## 5. Pemahaman Sistem Secara Keseluruhan

### Arsitektur End-to-End
SiCure adalah monolith yang di-deploy sebagai dua services terpisah (backend + frontend) di Railway dengan shared PostgreSQL database:

1. **User Action** (Frontend React): User klik "Submit PR" → React component collect form data + files → Axios POST ke `/api/v1/requisitions/`
2. **API Gateway** (Nginx/FastAPI): Request masuk → CORS check → JWT validation via `get_current_user()` dependency → Route ke handler function
3. **Business Logic** (Service Layer): Validate vendor quotes → Calculate totals → Check thresholds → Create PR record + line items + vendor quotes dalam atomic transaction
4. **Database** (PostgreSQL): Async session execute INSERT statements → Commit transaction → Return generated IDs
5. **Response**: Serialize models to Pydantic schemas → Wrap in envelope `{success, data, message}` → Return HTTP 201
6. **Logging**: Middleware capture request metadata → Generate correlation ID → Log as JSON → Propagate to all downstream logs

### Peran Tiap Modul
- **Auth Module** (`core/security.py`, `routers/auth.py`): Handle JWT creation/validation, password hashing, token blacklist. Critical security boundary.
- **Requisition Module** (`models/requisition.py`, `routers/requisitions.py`): Core domain logic. PR creation, editing, status transitions. Most complex module.
- **PO Module** (`models/purchase_order.py`, `routers/purchase_orders.py`): Auto-generate PO saat admin approve PR. Link PR → PO → Vendor.
- **GRN Module** (`models/grn.py`, `routers/grn.py`): Goods receipt tracking. File upload untuk invoice + foto barang. Verification workflow.
- **Middleware** (`main.py`): Cross-cutting concerns — CORS, auth, logging, error handling. Applied globally.

### CI/CD Pipeline
Setiap push ke `main` trigger GitHub Actions workflow:
1. **Checkout**: Pull code dari repository
2. **Test Parallel**: Backend pytest (45 tests, 95% coverage) + Frontend vitest (45 tests) jalan bersamaan
3. **Build Docker**: Jika test pass, build multi-stage Docker images (optimized size)
4. **Deploy Verify**: Hit health endpoint di Railway untuk confirm deployment success

Pipeline ini ensure code quality gate — no broken code reach production. Average CI time ~3 minutes thanks to parallel execution dan dependency caching.

### Deployment Railway
Railway abstract away infrastructure complexity. Kita cukup:
- Connect GitHub repo → Railway auto-detect Dockerfile
- Set environment variables (DATABASE_URL, JWT secrets, CORS origins)
- Push ke main → Railway auto-build image → Deploy new container → Health check → Switch traffic

Zero-downtime deployment handled automatically. Database migrations run on startup via Alembic. Monitoring via Railway dashboard + structured logs.

### Bagian Non-Backend yang Saya Pahami
Meski fokus backend, saya perlu understand full stack untuk effective collaboration:
- **Frontend**: React components consume our API. State management via Context API. TypeScript type safety match our Pydantic schemas. Vite for fast HMR during development.
- **DevOps**: Docker Compose orchestrate local development. Multi-stage builds optimize image size. Nginx reverse proxy handle routing. Railway handle production scaling.
- **QA**: Comprehensive test strategy — unit tests isolate logic, integration tests verify end-to-end flows, property-based tests (Hypothesis) find edge cases. Coverage threshold enforce quality.
