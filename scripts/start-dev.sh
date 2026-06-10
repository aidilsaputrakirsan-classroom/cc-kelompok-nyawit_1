#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SiCure - Starting Development Environment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your configuration before continuing.${NC}"
    echo -e "${YELLOW}⚠️  Especially update JWT_SECRET and POSTGRES_PASSWORD${NC}"
    exit 1
fi

echo -e "${GREEN}📦 Building Docker images...${NC}"
docker compose build

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"
echo ""
echo -e "${GREEN}🚀 Starting services...${NC}"
docker compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

# First setup detection - seed database only on first run
if [ ! -f .dev_setup_complete ]; then
    echo ""
    echo -e "${YELLOW}🌱 First setup detected!${NC}"
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 15
    
    echo -e "${YELLOW}Running initial database seed...${NC}"
    docker compose exec -T -e SEED_ON_STARTUP=true backend python -m app.seed
    
    if [ $? -eq 0 ]; then
        touch .dev_setup_complete
        echo -e "${GREEN}✓ Initial seeding completed${NC}"
        echo -e "${GREEN}✓ Setup complete marker created${NC}"
    else
        echo -e "${RED}✗ Seeding failed. You can retry manually:${NC}"
        echo -e "  docker compose exec backend python -m app.seed"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "🌐 Frontend: ${GREEN}http://localhost:${FRONTEND_PORT:-5173}${NC}"
echo -e "🔧 Backend API: ${GREEN}http://localhost:${BACKEND_PORT:-8000}${NC}"
echo -e "📊 API Docs: ${GREEN}http://localhost:${BACKEND_PORT:-8000}/docs${NC}"
echo -e "💾 Database: ${GREEN}localhost:${DB_PORT:-5432}${NC}"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo -e "  docker compose logs -f"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo -e "  docker compose down"
echo ""
echo -e "${YELLOW}To seed database:${NC}"
echo -e "  docker compose exec backend python -m app.seed"
echo ""