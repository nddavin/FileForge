# FileForge Docker Makefile
.PHONY: help build up down logs shell test clean prod

# Default target
help:
	@echo "FileForge Docker Commands:"
	@echo "  make build     - Build all Docker images"
	@echo "  make up        - Start all services in development mode"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - View logs from all services"
	@echo "  make shell     - Open shell in API container"
	@echo "  make test      - Run tests in Docker"
	@echo "  make clean     - Remove all containers and volumes"
	@echo "  make prod      - Start services in production mode"
	@echo "  make migrate   - Run database migrations"
	@echo "  make seed      - Seed database with test data"

# Build all images
build:
	docker-compose build

# Start development services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# API container shell
shell:
	docker-compose exec api /bin/bash

# Database shell
db-shell:
	docker-compose exec postgres psql -U user -d fileforge

# Run tests
test:
	docker-compose exec api pytest

# Clean everything
clean:
	docker-compose down -v --rmi all --remove-orphans

# Production mode
prod:
	docker-compose -f docker-compose.prod.yml up -d

# Production build
prod-build:
	docker-compose -f docker-compose.prod.yml build

# Production down
prod-down:
	docker-compose -f docker-compose.prod.yml down

# Database migrations
migrate:
	docker-compose exec api alembic upgrade head

# Create migration
create-migration:
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

# Seed database
seed:
	docker-compose exec api python -c "from file_processor.database import seed_db; seed_db()"

# Restart services
restart:
	docker-compose restart

# Pull latest images
pull:
	docker-compose pull

# Show status
status:
	docker-compose ps
