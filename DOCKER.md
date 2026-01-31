# FileForge Docker Setup

Complete containerization setup for FileForge with Docker and Docker Compose.

## Quick Start

```bash
# Start all services
docker-compose up -d

# Or use Make
make up
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FileForge Stack                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │    │     API      │    │    Worker    │  │
│  │   (Vite)     │◄──►│  (FastAPI)   │◄──►│   (Celery)   │  │
│  │   Port 3000  │    │   Port 8000  │    │              │  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘  │
│                             │                               │
│                             ▼                               │
│                      ┌──────────────┐                      │
│                      │    Beat      │                      │
│                      │  (Scheduler) │                      │
│                      └──────────────┘                      │
│                             │                               │
│              ┌──────────────┼──────────────┐               │
│              ▼              ▼              ▼               │
│       ┌──────────┐   ┌──────────┐   ┌──────────┐          │
│       │ Postgres │   │  Redis   │   │ Uploads  │          │
│       │  Port    │   │  Port    │   │  Volume  │          │
│       │  5432    │   │  6379    │   │          │          │
│       └──────────┘   └──────────┘   └──────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Services

| Service | Description | Port | Image |
|---------|-------------|------|-------|
| `api` | FastAPI backend | 8000 | fileforge/api |
| `worker` | Celery worker | - | fileforge/worker |
| `beat` | Celery scheduler | - | fileforge/beat |
| `frontend` | Vite React frontend | 3000 | fileforge/frontend |
| `postgres` | PostgreSQL database | 5432 | postgres:15-alpine |
| `redis` | Redis cache/queue | 6379 | redis:7-alpine |

## Development

### Using Make (Recommended)

```bash
# Build all images
make build

# Start services
make up

# View logs
make logs

# Run tests
make test

# Database shell
make db-shell

# API shell
make shell

# Stop everything
make down

# Clean up (removes volumes)
make clean
```

### Using Docker Compose Directly

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head

# Run tests
docker-compose exec api pytest

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Production

```bash
# Copy environment file
cp .env.example .env

# Edit .env with production values
nano .env

# Start production services
make prod

# Or directly
docker-compose -f docker-compose.prod.yml up -d
```

### Production Environment Variables

Create `.env` file:

```bash
# Database
POSTGRES_USER=fileforge
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=fileforge
DATABASE_URL=postgresql://fileforge:secure_password@postgres:5432/fileforge

# Redis
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Building Images

### Individual Images

```bash
# Backend
docker build -t fileforge/api:latest ./backend

# Frontend
docker build -t fileforge/frontend:latest ./frontend

# Full stack (monolithic)
docker build -t fileforge/app:latest .
```

### Pushing to Registry

```bash
# Tag for registry
docker tag fileforge/api:latest your-registry.com/fileforge/api:latest
docker tag fileforge/frontend:latest your-registry.com/fileforge/frontend:latest

# Push
docker push your-registry.com/fileforge/api:latest
docker push your-registry.com/fileforge/frontend:latest
```

## Data Persistence

Volumes are used for data persistence:

| Volume | Purpose | Backup |
|--------|---------|--------|
| `postgres_data` | Database files | Yes |
| `redis_data` | Redis persistence | Optional |
| `uploads_data` | User uploads | Yes |

### Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U user fileforge > backup.sql

# Backup uploads
docker run --rm -v fileforge_uploads_data:/data -v $(pwd):/backup alpine tar czf /backup/uploads.tar.gz -C /data .
```

### Restore

```bash
# Restore PostgreSQL
docker-compose exec -T postgres psql -U user fileforge < backup.sql

# Restore uploads
docker run --rm -v fileforge_uploads_data:/data -v $(pwd):/backup alpine tar xzf /backup/uploads.tar.gz -C /data
```

## Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# View health check logs
docker-compose exec api curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :8000

# Or change port in docker-compose.yml
```

**Database connection failed:**
```bash
# Check postgres logs
docker-compose logs postgres

# Verify credentials
docker-compose exec postgres psql -U user -d fileforge
```

**Celery worker not processing:**
```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### Reset Everything

```bash
# Stop and remove everything
make clean

# Or manually
docker-compose down -v --rmi all --remove-orphans
```

## Scaling

### Development

```bash
# Scale workers
docker-compose up -d --scale worker=3
```

### Production (with Swarm)

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml fileforge

# Scale service
docker service scale fileforge_worker=5
```

## Advanced Configuration

### Custom Networks

```yaml
# docker-compose.override.yml
networks:
  fileforge-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Resource Limits

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Security

- Non-root user in containers
- Secrets mounted as files
- Network isolation
- Health checks enabled
- Security headers in nginx

## CI/CD Integration

```yaml
# .github/workflows/docker.yml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build
        run: docker-compose build
      
      - name: Test
        run: docker-compose run --rm api pytest
```

## Support

For issues or questions:
- Check logs: `make logs`
- Open shell: `make shell`
- Documentation: [docs/README.md](docs/README.md)
