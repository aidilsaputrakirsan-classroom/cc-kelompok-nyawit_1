#!/bin/bash
# Log helper script untuk debugging microservices
# Usage: ./scripts/logs.sh [command] [args]

COMPOSE_FILE="docker-compose.microservices.yml"

case "$1" in
  all)
    echo "📋 Showing all service logs..."
    docker compose -f "$COMPOSE_FILE" logs -f auth-service procurement-service
    ;;
  errors)
    echo "❌ Showing ERROR logs only..."
    docker compose -f "$COMPOSE_FILE" logs auth-service procurement-service 2>&1 | grep '"level":"ERROR"'
    ;;
  trace)
    if [ -z "$2" ]; then
      echo "Usage: ./scripts/logs.sh trace <correlation-id>"
      exit 1
    fi
    echo "🔗 Tracing correlation ID: $2"
    docker compose -f "$COMPOSE_FILE" logs auth-service procurement-service 2>&1 | grep "$2"
    ;;
  metrics)
    echo "📊 Fetching metrics..."
    echo "--- Auth Service ---"
    curl -s http://localhost/auth/metrics | python3 -m json.tool
    echo ""
    echo "--- Procurement Service ---"
    curl -s http://localhost/api/metrics | python3 -m json.tool
    ;;
  export)
    mkdir -p logs
    FILE="logs/all-services-$(date +%Y%m%d-%H%M%S).log"
    docker compose -f "$COMPOSE_FILE" logs --no-color auth-service procurement-service > "$FILE"
    echo "📁 Logs exported to: $FILE"
    ;;
  *)
    echo "Usage: ./scripts/logs.sh {all|errors|trace <id>|metrics|export}"
    ;;
esac
