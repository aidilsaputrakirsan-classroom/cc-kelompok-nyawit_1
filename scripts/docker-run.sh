#!/bin/bash

# ============================================================
# Script untuk menjalankan semua container secara manual
# CATATAN: Minggu 7 kita akan pakai Docker Compose yang lebih elegan
# ============================================================

ACTION=${1:-start}

case $ACTION in
  start)
    echo "🚀 Starting all containers..."
    
    # Create network
    docker network create cloudnet 2>/dev/null || true
    
    # Database
    echo "📦 Starting database..."
    docker run -d \
      --name db \
      --network cloudnet \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=pgbaqi \
      -e POSTGRES_DB=sicure \
      -p 5433:5432 \
      -v pgdata:/var/lib/postgresql/data \
      postgres:16-alpine
    
    # Wait for database to be ready
    echo "⏳ Waiting for database..."
    sleep 5
    
    # Backend
    echo "🐍 Starting backend..."
    docker run -d \
      --name backend \
      --network cloudnet \
      --env-file backend/.env.docker \
      -p 8000:8000 \
      cloudapp-backend:v2
    
    # Frontend
    echo "⚛️ Starting frontend..."
    docker run -d \
      --name frontend \
      --network cloudnet \
      -p 3000:80 \
      cloudapp-frontend:v1
    
    echo ""
    echo "✅ All containers started!"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   Database: localhost:5433"
    ;;
    
  stop)
    echo "🛑 Stopping all containers..."
    docker stop frontend backend db 2>/dev/null
    docker rm frontend backend db 2>/dev/null
    echo "✅ All containers stopped and removed."
    ;;
    
  status)
    echo "📊 Container Status:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    ;;
    
  logs)
    CONTAINER=${2:-backend}
    echo "📋 Logs for $CONTAINER:"
    docker logs -f $CONTAINER
    ;;
    
  *)
    echo "Usage: ./scripts/docker-run.sh [start|stop|status|logs [container]]"
    ;;
esac