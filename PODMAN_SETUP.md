# ISO 20022 GenAI Migration Platform - Podman Setup Guide

This guide explains how to run the ISO 20022 GenAI Migration Platform using **Podman** - a container orchestration platform compatible with Docker but with additional rootless security benefits.

## Prerequisites

### Install Podman

**macOS:**
```bash
brew install podman
```

**Linux (Fedora/RHEL/CentOS):**
```bash
sudo dnf install -y podman
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install -y podman
```

**Windows (via WSL2):**
```powershell
# Using Chocolatey
choco install podman

# Or download from: https://podman.io/docs/installation
```

### Install podman-compose

```bash
pip install podman-compose
```

Or if you prefer to use docker-compose with Podman:
```bash
# Create an alias to use docker-compose with Podman socket
sudo ln -s /usr/bin/podman /usr/bin/docker
```

## Quick Start

### Option 1: Automated Setup (Recommended)

**On macOS/Linux:**
```bash
chmod +x podman-setup.sh
./podman-setup.sh
```

**On Windows:**
```cmd
podman-setup.bat
```

This will:
- ✓ Check Podman installation
- ✓ Create `.env` file from `.env.example`
- ✓ Build container images
- ✓ Start all services
- ✓ Show endpoint information

### Option 2: Manual Setup

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Build images:**
   ```bash
   podman-compose -f docker-compose.yml build
   ```

3. **Start services:**
   ```bash
   podman-compose -f docker-compose.yml up -d
   ```

4. **Verify services are running:**
   ```bash
   podman-compose -f docker-compose.yml ps
   ```

## Using Make Commands (Linux/macOS)

The `Makefile` provides convenient commands:

```bash
make help              # Show all available commands
make build             # Build container images
make up                # Start services (background)
make up-foreground     # Start services (foreground)
make down              # Stop services
make logs              # View logs from all services
make logs-backend      # View backend logs only
make logs-frontend     # View frontend logs only
make clean             # Remove containers, volumes, and images
make backend-shell     # Open shell in backend container
make db-shell          # Open PostgreSQL shell
make redis-cli         # Open Redis CLI
make status            # Show container status
```

## Service Endpoints

After starting the services, access them at:

| Service | URL | Purpose |
|---------|-----|---------|
| Backend | http://localhost:8000 | Main API server |
| API Docs | http://localhost:8000/docs | Swagger UI documentation |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Health | http://localhost:8000/health | Health check endpoint |
| Frontend | http://localhost:5173 | React UI application |
| Database | localhost:5432 | PostgreSQL (postgres:postgres) |
| Redis | localhost:6379 | Redis cache |
| Phoenix | http://localhost:6006 | Observability dashboard |

## Managing Services

### View Logs

```bash
# All services
podman-compose logs -f

# Specific service
podman-compose logs -f backend
podman-compose logs -f frontend
podman-compose logs -f postgres
```

### Access Service Shells

```bash
# Backend Python shell
podman-compose exec backend /bin/bash

# Frontend Node shell
podman-compose exec frontend /bin/sh

# PostgreSQL database
podman-compose exec postgres psql -U postgres -d iso_mapper

# Redis CLI
podman-compose exec redis redis-cli
```

### Stop Services

```bash
# Gracefully stop (containers remain)
podman-compose stop

# Stop and remove containers
podman-compose down

# Stop, remove containers, and delete volumes
podman-compose down -v
```

## Troubleshooting

### Services not starting

1. **Check logs:**
   ```bash
   podman-compose logs
   ```

2. **Verify Podman is running:**
   ```bash
   podman ps
   ```

3. **Rebuild images:**
   ```bash
   podman-compose down -v
   podman-compose build --no-cache
   podman-compose up -d
   ```

### Port conflicts

If ports are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Changed from 8000:8000
```

### Database connection issues

1. Check PostgreSQL is healthy:
   ```bash
   podman-compose exec postgres pg_isready -U postgres
   ```

2. Check environment variables:
   ```bash
   podman-compose exec backend env | grep DATABASE_URL
   ```

### Memory issues

If containers are being killed (OOMKilled), increase Docker/Podman memory:

```bash
# On macOS with Podman machine
podman machine set --memory 4096

# Check current settings
podman info | grep -A5 "host:"
```

## Configuration

### Environment Variables

Edit `.env` file to configure:

```bash
# App settings
APP_ENV=development
LOG_LEVEL=INFO
TRANSFORMATION_APPROACH=hybrid

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/iso_mapper

# Frontend
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Azure OpenAI (optional)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
```

### Volumes

Services use Docker volumes for persistence:

- `postgres_data` - Database persistence
- `redis_data` - Cache persistence
- `./app/v4_refactored` - Backend source code (mounted for live reload)
- `./ui/src` - Frontend source code (mounted for hot reload)

## Development Workflow

### Backend Changes

1. Edit files in `app/v4_refactored/`
2. Changes auto-reload via uvicorn
3. Check logs: `make logs-backend`

### Frontend Changes

1. Edit files in `ui/src/`
2. Vite hot-reload will update automatically
3. Check browser at http://localhost:5173

### Testing

```bash
# Run pytest in backend container
podman-compose exec backend pytest tests/ -v

# Run npm tests in frontend container
podman-compose exec frontend npm test
```

## Advanced Usage

### Build with custom image names

```bash
podman-compose -p my-project build
podman-compose -p my-project up -d
```

### Export/Import images

```bash
# Export
podman save iso-mapper-backend:latest -o iso-mapper-backend.tar

# Import
podman load -i iso-mapper-backend.tar
```

### Using rootless Podman

```bash
# Check if running rootless
podman info | grep rootless

# For rootless with port < 1024, use sudo or reconfigure ports
# Restart with high ports (> 1024)
podman-compose down
# Edit docker-compose.yml ports to use > 1024
podman-compose up -d
```

## Getting Help

- **Podman Documentation:** https://podman.io/docs
- **podman-compose:** https://github.com/containers/podman-compose
- **API Docs:** http://localhost:8000/docs
- **Check service status:** `podman ps`

## Next Steps

1. ✓ Services are running
2. → Access frontend at http://localhost:5173
3. → Try transformation at `/transform` page
4. → Check API docs at http://localhost:8000/docs
5. → Implement business logic in backend services
6. → Add tests for validation
7. → Deploy to production with Podman or Kubernetes

## Cleanup

To completely remove all containers, images, and volumes:

```bash
make clean
```

Or manually:

```bash
podman-compose down -v
podman rmi iso-mapper-backend iso-mapper-frontend
```
