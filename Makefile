.PHONY: help build up down logs clean test

help:
	@echo "ISO 20022 Mapper - Podman Commands"
	@echo "===================================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help           Show this help message"
	@echo "  build          Build all container images"
	@echo "  up             Start all containers (background)"
	@echo "  up-foreground  Start all containers (foreground)"
	@echo "  down           Stop and remove all containers"
	@echo "  logs           Show logs from all containers"
	@echo "  logs-backend   Show logs from backend only"
	@echo "  logs-frontend  Show logs from frontend only"
	@echo "  clean          Remove containers, volumes, and images"
	@echo "  test           Run tests"
	@echo "  backend-shell  Open shell in backend container"
	@echo "  frontend-shell Open shell in frontend container"
	@echo "  db-shell       Open PostgreSQL shell"
	@echo "  redis-cli      Open Redis CLI"
	@echo "  status         Show container status"

build:
	@echo "Building containers with Podman..."
	podman-compose -f docker-compose.yml build

up:
	@echo "Starting containers with Podman (background)..."
	podman-compose -f docker-compose.yml up -d
	@echo ""
	@echo "Services running:"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Database: localhost:5432"
	@echo "  Redis:    localhost:6379"
	@echo "  Phoenix:  http://localhost:6006"

up-foreground:
	@echo "Starting containers with Podman (foreground)..."
	podman-compose -f docker-compose.yml up

down:
	@echo "Stopping containers..."
	podman-compose -f docker-compose.yml down

logs:
	podman-compose -f docker-compose.yml logs -f

logs-backend:
	podman-compose -f docker-compose.yml logs -f backend

logs-frontend:
	podman-compose -f docker-compose.yml logs -f frontend

clean:
	@echo "Cleaning up containers, volumes, and images..."
	podman-compose -f docker-compose.yml down -v
	podman rmi iso-mapper-backend iso-mapper-frontend 2>/dev/null || true
	@echo "Cleanup complete"

test:
	@echo "Running tests..."
	podman-compose -f docker-compose.yml exec backend pytest tests/ -v

backend-shell:
	podman-compose -f docker-compose.yml exec backend /bin/bash

frontend-shell:
	podman-compose -f docker-compose.yml exec frontend /bin/sh

db-shell:
	podman-compose -f docker-compose.yml exec postgres psql -U postgres -d iso_mapper

redis-cli:
	podman-compose -f docker-compose.yml exec redis redis-cli

status:
	@echo "Container status:"
	podman ps -a --filter "label=com.docker.compose.project=iso_mapper" || podman ps -a

version:
	@echo "Checking versions..."
	@podman --version
	@podman-compose --version
