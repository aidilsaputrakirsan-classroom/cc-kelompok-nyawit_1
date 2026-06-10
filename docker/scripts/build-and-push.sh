#!/bin/bash

# ============================================================
# SiCure - Build and Push to Docker Hub
# ============================================================
# This script builds Docker images and pushes them to Docker Hub
# Usage: ./scripts/build-and-push.sh [tag]
# Example: ./scripts/build-and-push.sh v1.0.0
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SiCure - Build & Push to Docker Hub${NC}"
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
read -p "Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled by user${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}📦 Step 1: Building Backend Image...${NC}"
docker build -t ${DOCKER_HUB_USERNAME}/sicure-backend:${IMAGE_TAG} -f backend/Dockerfile .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Backend build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Backend image built successfully${NC}"
echo ""

echo -e "${GREEN}📦 Step 2: Building Frontend Image...${NC}"
docker build -t ${DOCKER_HUB_USERNAME}/sicure-frontend:${IMAGE_TAG} -f frontend/Dockerfile .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Frontend build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend image built successfully${NC}"
echo ""

# Login to Docker Hub
echo -e "${GREEN}🔐 Step 3: Logging in to Docker Hub...${NC}"
docker login

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Docker Hub login failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Logged in successfully${NC}"
echo ""

# Push Backend Image
echo -e "${GREEN}🚀 Step 4: Pushing Backend Image to Docker Hub...${NC}"
docker push ${DOCKER_HUB_USERNAME}/sicure-backend:${IMAGE_TAG}

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to push backend image${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Backend image pushed successfully${NC}"
echo ""

# Push Frontend Image
echo -e "${GREEN}🚀 Step 5: Pushing Frontend Image to Docker Hub...${NC}"
docker push ${DOCKER_HUB_USERNAME}/sicure-frontend:${IMAGE_TAG}

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to push frontend image${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend image pushed successfully${NC}"
echo ""

# Also tag as latest if using version tag
if [ "$IMAGE_TAG" != "latest" ]; then
    echo -e "${GREEN}🏷️  Step 6: Tagging images as 'latest'...${NC}"
    
    docker tag ${DOCKER_HUB_USERNAME}/sicure-backend:${IMAGE_TAG} ${DOCKER_HUB_USERNAME}/sicure-backend:latest
    docker tag ${DOCKER_HUB_USERNAME}/sicure-frontend:${IMAGE_TAG} ${DOCKER_HUB_USERNAME}/sicure-frontend:latest
    
    echo -e "${GREEN}🚀 Pushing 'latest' tags...${NC}"
    docker push ${DOCKER_HUB_USERNAME}/sicure-backend:latest
    docker push ${DOCKER_HUB_USERNAME}/sicure-frontend:latest
    
    echo -e "${GREEN}✓ Latest tags pushed${NC}"
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ BUILD & PUSH COMPLETED!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Images available at:${NC}"
echo -e "  https://hub.docker.com/r/${DOCKER_HUB_USERNAME}/sicure-backend"
echo -e "  https://hub.docker.com/r/${DOCKER_HUB_USERNAME}/sicure-frontend"
echo ""
echo -e "${YELLOW}To deploy with these images:${NC}"
echo -e "  DOCKER_HUB_USERNAME=${DOCKER_HUB_USERNAME} IMAGE_TAG=${IMAGE_TAG} docker compose -f docker-compose.prod.yml up -d"
echo ""
