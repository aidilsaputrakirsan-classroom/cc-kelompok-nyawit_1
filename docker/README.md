# Docker & Infrastructure

This folder contains all Docker-related configurations, scripts, and documentation for the project.

## 📁 Folder Structure

```
docker/
├── compose/              # Docker Compose configurations
│   ├── docker-compose.yml          # Development environment
│   └── docker-compose.prod.yml     # Production overrides
├── dockerfiles/          # Dockerfile copies for reference
│   ├── Dockerfile.backend          # Backend service Dockerfile
│   ├── Dockerfile.frontend         # Frontend production Dockerfile
│   └── Dockerfile.frontend.dev     # Frontend development Dockerfile
├── scripts/              # Docker management scripts
│   ├── build-and-push.sh           # Build and push images to registry
│   ├── deploy-from-hub.sh          # Deploy from Docker Hub
│   ├── start-dev.sh                # Start development environment
│   └── stop-dev.sh                 # Stop development environment
└── README.md             # This file
```

**Note:** The actual Dockerfiles remain in their respective service folders (`backend/Dockerfile`, `frontend/Dockerfile`) for backward compatibility and standard Docker practices. Copies here are for documentation purposes.

## 🚀 Quick Start

### Development Environment

1. **Start all services:**
   ```bash
   # From project root
   docker/compose/start-dev.sh
   
   # Or manually
   cd docker/compose
   docker compose up -d
   ```

2. **Access services:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PostgreSQL: localhost:5432

3. **View logs:**
   ```bash
   docker compose logs -f
   docker compose logs -f backend
   docker compose logs -f frontend
   docker compose logs -f postgres
   ```

4. **Stop services:**
   ```bash
   docker/compose/stop-dev.sh
   
   # Or manually
   docker compose down
   ```

### Production Deployment

1. **Build production images:**
   ```bash
   docker/compose/scripts/build-and-push.sh
   ```

2. **Deploy with production config:**
   ```bash
   docker compose -f docker/compose/docker-compose.yml \
                  -f docker/compose/docker-compose.prod.yml \
                  up -d
   ```

## 📋 Services

### PostgreSQL Database
- **Image:** `postgres:16-alpine`
- **Port:** 5432
- **Data Volume:** `postgres_data` (persistent)
- **Health Check:** Automatic database readiness check

### Backend (FastAPI)
- **Build Context:** `../../backend/`
- **Port:** 8000
- **Features:**
  - Automatic database migrations on startup
  - Hot reload in development
  - Upload volume mounted for file storage
- **Environment Variables:** See `.env.example` at project root

### Frontend (React + Vite)
- **Development Build:** Uses `Dockerfile.dev` with hot reload
- **Production Build:** Uses `Dockerfile` with Nginx
- **Port:** 5173 (dev), 80 (prod)
- **Features:**
  - Volume mounting for live code changes
  - Node modules preserved in container

## 🔧 Scripts

### `start-dev.sh`
Starts the development environment with proper error handling and status checks.

```bash
./docker/scripts/start-dev.sh
```

### `stop-dev.sh`
Stops all containers and removes them (preserves data volumes).

```bash
./docker/scripts/stop-dev.sh
```

### `build-and-push.sh`
Builds Docker images and pushes them to Docker Hub.

```bash
./docker/scripts/build-and-push.sh [TAG]
```

**Required environment variables:**
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

### `deploy-from-hub.sh`
Pulls and deploys images from Docker Hub.

```bash
./docker/scripts/deploy-from-hub.sh [TAG]
```

## 🐳 Docker Commands Reference

### Common Commands

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View images
docker images

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# View network
docker network ls

# Inspect container
docker inspect <container_name>

# Execute command in running container
docker exec -it sicure-backend bash
docker exec -it sicure-postgres psql -U sicure_user -d sicure_db
```

### Database Management

```bash
# Access PostgreSQL shell
docker exec -it sicure-postgres psql -U sicure_user -d sicure_db

# Backup database
docker exec sicure-postgres pg_dump -U sicure_user sicure_db > backup.sql

# Restore database
cat backup.sql | docker exec -i sicure-postgres psql -U sicure_user -d sicure_db

# View database size
docker exec sicure-postgres psql -U sicure_user -d sicure_db -c "SELECT pg_size_pretty(pg_database_size('sicure_db'));"
```

### Debugging

```bash
# Check container resource usage
docker stats

# View container logs
docker logs sicure-backend --tail 100 -f

# Inspect container network
docker inspect sicure-backend | grep -A 20 "NetworkSettings"

# Check volume usage
docker system df -v
```

## 🔐 Security Best Practices

1. **Never commit sensitive data:**
   - Use `.env` files for secrets
   - Add `.env` to `.gitignore`
   - Use `.env.example` as template

2. **Production considerations:**
   - Don't expose database port to host
   - Use strong passwords
   - Enable SSL/TLS
   - Regular security updates

3. **Volume permissions:**
   - Ensure proper ownership of mounted volumes
   - Use specific user IDs in production

## 📊 Monitoring

### Health Checks
All services have health checks configured:
- PostgreSQL: Database connection test
- Backend: HTTP health endpoint
- Frontend: HTTP response check

### Viewing Health Status
```bash
docker inspect --format='{{.State.Health.Status}}' sicure-postgres
docker inspect --format='{{.State.Health.Status}}' sicure-backend
```

## 🔄 CI/CD Integration

The Docker configuration is integrated with GitHub Actions:
- Automated builds on push to main branch
- Image tagging with git SHA
- Automated deployment to staging/production
- Security scanning of images

See `.github/workflows/ci.yml` for details.

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker logs <container_name>

# Check if port is in use
lsof -i :8000
lsof -i :5173
lsof -i :5432
```

### Database connection issues
```bash
# Verify database is healthy
docker inspect sicure-postgres | grep -A 10 Health

# Test connection from backend
docker exec sicure-backend python -c "import asyncpg; print('OK')"
```

### Permission errors with volumes
```bash
# Fix ownership
sudo chown -R $(whoami):$(whoami) backend/uploads
```

### Rebuild without cache
```bash
docker compose build --no-cache
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [React Docker Best Practices](https://mherman.org/blog/dockerizing-a-react-app/)

## 🤝 Contributing

When modifying Docker configuration:
1. Test changes locally first
2. Update this README if adding new features
3. Ensure `.env.example` reflects new environment variables
4. Verify production deployment still works
5. Update CI/CD workflows if needed
