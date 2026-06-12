# ══════════════════════════════════════════════════════════════════
# Makefile — SiCure (Monolith)
# Kelompok Nyawit
# ══════════════════════════════════════════════════════════════════
# Mempermudah menjalankan aplikasi monolith (backend + frontend + db)
# via Docker Compose untuk pengembangan lokal.
#
# Usage:
#   make up      → Start semua container (build jika perlu)
#   make down    → Stop & hapus container
#   make logs    → Stream logs semua service
#   make ps      → Status container
#   make seed    → Seed database (user demo)
# ══════════════════════════════════════════════════════════════════

.PHONY: help up down restart logs ps build seed clean

COMPOSE := docker compose

help:
	@echo "SiCure (Monolith) — Makefile"
	@echo ""
	@echo "  make up       - Start backend + frontend + postgres"
	@echo "  make down     - Stop & remove containers"
	@echo "  make restart  - Restart semua service"
	@echo "  make logs     - Stream logs semua service"
	@echo "  make ps       - Status container"
	@echo "  make build    - Rebuild image"
	@echo "  make seed     - Seed database (user demo)"
	@echo "  make clean    - Stop & hapus container + volume (DATA HILANG)"

up:
	$(COMPOSE) up -d --build
	@echo "✅ Backend: http://localhost:8000  | Frontend: http://localhost:5173"

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

build:
	$(COMPOSE) build --no-cache

seed:
	$(COMPOSE) exec backend python -m app.seed

clean:
	$(COMPOSE) down -v
