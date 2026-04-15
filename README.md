# SiCure — Sistem Procurement

Aplikasi procurement berbasis web dengan **FastAPI** (backend) dan **React + Vite** (frontend).

## Prasyarat

- [mise](https://mise.jdx.dev/) (mengelola versi Python & Node.js)
- PostgreSQL (atau database lain yang kompatibel)

## Quick Start

```bash
# 1. Masuk ke direktori project
cd sicure

# 2. Aktifkan toolchain via mise (otomatis install Python 3.11 & Node 20)
mise install
mise trust

# 3. Setup backend
cd backend
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # edit sesuai konfigurasi lokal
cd ..

# 4. Setup frontend
cd frontend
npm install
cd ..
```

## Menjalankan Project

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs tersedia di: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm run dev
```

Aplikasi tersedia di: `http://localhost:5173`

## Menjalankan via mise (tasks)

```bash
# Dari root project
mise run backend   # jalankan backend
mise run frontend  # jalankan frontend
```

## Struktur Project

```
sicure/
├── mise.toml
├── .env.example
├── README.md
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── venv/
│   └── app/
│       ├── main.py
│       ├── core/        # config, security, dependencies
│       ├── db/          # database session & base
│       ├── models/      # SQLAlchemy models
│       ├── schemas/     # Pydantic schemas
│       ├── routers/     # API route handlers
│       └── utils/       # helper functions
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        └── ...
```
