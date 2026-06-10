# ══════════════════════════════════════════════════════════════════
# Makefile — SiCure Microservices
# Kelompok Nyawit
# ══════════════════════════════════════════════════════════════════
#
# Mempermudah management Docker Compose untuk arsitektur microservices.
# Tugas Modul 12: Lead DevOps membuat Makefile dengan target:
#   up, down, logs, restart, plus helpers lainnya.
#
# Usage:
#   make up          → Start semua services
#   make down        → Stop semua services
#   make logs        → Lihat logs semua services (follow mode)
#   make restart     → Restart semua services
#   make ps          → Lihat status containers
#   make seed        → Jalankan seeder Auth Service
# ══════════════════════════════════════════════════════════════════

.PHONY: help up down restart logs ps build clean seed test health

# Default compose file
COMPOSE_FILE := docker-compose.microservices.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

# ── Help (default target) ─────────────────────────────────────────
help:
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║          SiCure Microservices — Makefile Help            ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 Main Commands:"
	@echo "  make up          - Start all microservices (build if needed)"
	@echo "  make down        - Stop and remove all containers"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - Stream logs from all services"
	@echo ""
	@echo "🔍 Monitoring:"
	@echo "  make ps          - Show container status"
	@echo "  make health      - Check health of all services"
	@echo ""
	@echo "🛠️  Development:"
	@echo "  make build       - Rebuild all service images"
	@echo "  make seed        - Run Auth Service seeder"
	@echo "  make clean       - Stop & remove containers + volumes (⚠️  data loss)"
	@echo ""
	@echo "📋 Individual Service Logs:"
	@echo "  make logs-auth       - Auth Service logs"
	@echo "  make logs-proc       - Procurement Service logs"
	@echo "  make logs-gateway    - Gateway logs"
	@echo ""

# ── Main Commands ─────────────────────────────────────────────────

up: ## Start all microservices
	@echo "🚀 Starting SiCure microservices..."
	$(COMPOSE) up -d --build
	@echo ""
	@echo "✅ All services started!"
	@echo "   Gateway: http://localhost"
	@echo "   Auth Service: http://localhost/api/v1/auth/health"
	@echo "   Procurement Service: http://localhost/api/v1/requisitions/"
	@echo ""
	@echo "Run 'make logs' to see logs or 'make ps' to check status."

down: ## Stop and remove all containers
	@echo "🛑 Stopping all services..."
	$(COMPOSE) down
	@echo "✅ All services stopped."

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	$(COMPOSE) restart
	@echo "✅ All services restarted."

logs: ## Stream logs from all services (Ctrl+C to exit)
	$(COMPOSE) logs -f

# ── Monitoring ────────────────────────────────────────────────────

ps: ## Show container status
	@echo "📊 Container Status:"
	@$(COMPOSE) ps

health: ## Check health of all services
	@echo "🏥 Service Health Check:"
	@echo ""
	@echo "┌─ Gateway ────────────────────────────────────────┐"
	@curl -s http://localhost/health | python3 -m json.tool 2>/dev/null || echo "❌ Gateway not responding"
	@echo "└──────────────────────────────────────────────────┘"
	@echo ""
	@echo "┌─ Auth Service ───────────────────────────────────┐"
	@curl -s http://localhost/api/v1/auth/health | python3 -m json.tool 2>/dev/null || echo "❌ Auth Service not responding"
	@echo "└──────────────────────────────────────────────────┘"
	@echo ""
	@echo "┌─ Procurement Service ────────────────────────────┐"
	@curl -s http://localhost/api/v1/requisitions/admin/categories -H "Authorization: Bearer test" 2>&1 | head -3 || echo "⚠️  Requires auth token"
	@echo "└──────────────────────────────────────────────────┘"

# ── Development ───────────────────────────────────────────────────

build: ## Rebuild all service images
	@echo "🔨 Rebuilding all service images..."
	$(COMPOSE) build --no-cache
	@echo "✅ Build complete."

seed: ## Run Auth Service seeder (create demo users)
	@echo "🌱 Running Auth Service seeder..."
	$(COMPOSE) exec auth-service python seed.py
	@echo ""
	@echo "✅ Seeding complete!"
	@echo "   Credentials:"
	@echo "     admin@sicure.com / admin1234 (Admin)"
	@echo "     requester1@sicure.com / requester1234 (Requester)"
	@echo "     requester2@sicure.com / requester1234 (Requester)"

clean: ## Stop, remove containers & volumes (⚠️  ALL DATA WILL BE LOST)
	@echo "⚠️  WARNING: This will delete all containers and volumes (data loss)!"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "🗑️  Cleaning up..."; \
		$(COMPOSE) down -v; \
		echo "✅ Cleanup complete. All data removed."; \
	else \
		echo "❌ Cancelled."; \
	fi

# ── Individual Service Logs ───────────────────────────────────────

logs-auth: ## Auth Service logs only
	$(COMPOSE) logs -f auth-service

logs-proc: ## Procurement Service logs only
	$(COMPOSE) logs -f procurement-service

logs-gateway: ## Gateway logs only
	$(COMPOSE) logs -f gateway

logs-frontend: ## Frontend logs only
	$(COMPOSE) logs -f frontend

logs-db: ## Database logs (both auth-db & procurement-db)
	$(COMPOSE) logs -f auth-db procurement-db

# ── Shortcuts ─────────────────────────────────────────────────────

shell-auth: ## Open shell in Auth Service container
	$(COMPOSE) exec auth-service /bin/sh

shell-proc: ## Open shell in Procurement Service container
	$(COMPOSE) exec procurement-service /bin/sh

shell-gateway: ## Open shell in Gateway container
	$(COMPOSE) exec gateway /bin/sh

# ── Testing ───────────────────────────────────────────────────────

test: ## Run basic smoke test (health checks)
	@echo "🧪 Running smoke tests..."
	@echo -n "Gateway health... "
	@curl -sf http://localhost/health > /dev/null && echo "✅" || echo "❌"
	@echo -n "Auth Service health... "
	@curl -sf http://localhost/api/v1/auth/health > /dev/null && echo "✅" || echo "❌"
	@echo ""
	@echo "✅ Smoke tests complete."
