#!/bin/bash

# ============================================================
# SiCure - Deploy from Docker Hub
# ============================================================
# This script pulls images from Docker Hub and deploys the app
# Usage: ./scripts/deploy-from-hub.sh [tag]
# Example: ./scripts/deploy-from-hub.sh v1.0.0
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SiCure - Deploy from Docker Hub${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ Error: .env file not found${NC}"
    echo -e "${YELLOW}  Please create .env file from .env.example${NC}"
    exit 1
fi

# Load environment variables
source .env

# Get Docker Hub username
DOCKER_HUB_USERNAME=${DOCKER_HUB_USERNAME:-""}

if [ -z "$DOCKER_HUB_USERNAME" ]; then
    echo -e "${YELLOW}⚠️  DOCKER_HUB_USERNAME not set in .env${NC}"
    read -p "Enter your Docker Hub username: " DOCKER_HUB_USERNAME
    export DOCKER_HUB_USERNAME
fi

# Get image tag
IMAGE_TAG=${1:-latest}

echo -e "${GREEN}Configuration:${NC}"
echo -e "  Docker Hub Username: ${BLUE}${DOCKER_HUB_USERNAME}${NC}"
echo -e "  Image Tag: ${BLUE}${IMAGE_TAG}${NC}"
echo -e "  Backend Image: ${BLUE}${DOCKER_HUB_USERNAME}/sicure-backend:${IMAGE_TAG}${NC}"
echo -e "  Frontend Image: ${BLUE}${DOCKER_HUB_USERNAME}/sicure-frontend:${IMAGE_TAG}${NC}"
echo ""

# Confirm before proceeding
read -p "Continue with deployment? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled by user${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}📥 Step 1: Pulling latest images from Docker Hub...${NC}"

export DOCKER_HUB_USERNAME
export IMAGE_TAG

docker compose -f docker-compose.prod.yml pull backend frontend

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to pull images${NC}"
    echo -e "${YELLOW}  Make sure images exist on Docker Hub${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Images pulled successfully${NC}"
echo ""

echo -e "${GREEN}🚀 Step 2: Stopping existing services...${NC}"
docker compose -f docker-compose.prod.yml down

echo -e "${GREEN}✓ Services stopped${NC}"
echo ""

echo -e "${GREEN}🚀 Step 3: Starting services with new images...${NC}"
docker compose -f docker-compose.prod.yml up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Services started${NC}"
echo ""

echo -e "${GREEN}⏳ Step 4: Waiting for services to be healthy...${NC}"
sleep 10

# Check service status
echo -e "${GREEN}📊 Service Status:${NC}"
docker compose -f docker-compose.prod.yml ps

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ DEPLOYMENT COMPLETED!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Access your application:${NC}"
echo -e "  Frontend: http://localhost:${FRONTEND_PORT:-80}"
echo -e "  Backend:  http://localhost:${BACKEND_PORT:-8000}"
echo -e "  API Docs: http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo -e "  docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo -e "  docker compose -f docker-compose.prod.yml down"
echo ""
