# ISO 20022 GenAI Migration Platform - Setup & Running Guide

This document explains how to run the ISO 20022 GenAI Migration Platform application using Podman containers.

## 📁 Project Structure & Requirements Files

The project contains multiple `requirements.txt` files for different versions:

### Main Dependencies Files

| Location | Purpose |
|----------|---------|
| `app/v4_refactored/requirements.txt` | **Main backend (recommended)** - FastAPI, LangGraph, Azure OpenAI, observability |
| `app/v4/requirements.txt` | Previous version (v4) |
| `app/v3/requirements.txt` | Previous version (v3) |
| `app/v2/requirements.txt` | Previous version (v2) |
| `app/v2/mt_mx_api/requirements.txt` | v2 API-specific dependencies |

### Root Requirements File

| Location | Purpose |
|----------|---------|
| `../requirements.txt` | PayOrch project dependencies (parent project) |

**Recommended:** Use `app/v4_refactored/requirements.txt` - it's the latest refactored version aligned with PayOrch standards.

## 🚀 Quick Start with Podman

### Prerequisites

1. **Install Podman:**
   - macOS: `brew install podman`
   - Linux: `sudo apt-get install podman` or `sudo dnf install podman`
   - Windows: Download from https://podman.io/docs/installation

2. **Install podman-compose:**
   ```bash
   pip install podman-compose
   ```

### Automated Setup (Recommended)

**macOS/Linux:**
```bash
chmod +x podman-setup.sh
./podman-setup.sh
```

**Windows:**
```cmd
podman-setup.bat
```

### Manual Setup

1. **Clone/prepare environment:**
   ```bash
   cd iso_mapper
   cp .env.example .env
   ```

2. **Build containers:**
   ```bash
   podman-compose build
   ```

3. **Start services:**
   ```bash
   podman-compose up -d
   ```

4. **View status:**
   ```bash
   podman-compose ps
   ```

## 🛠️ Make Commands (Linux/macOS)

```bash
make help                  # Show all commands
make build                 # Build container images
make up                    # Start services
make down                  # Stop services
make logs                  # View all logs
make logs-backend          # View backend logs
make backend-shell         # Open backend shell
make db-shell              # Open database shell
make status                # Show container status
make clean                 # Remove everything
```

## 📊 Service Endpoints

Once running, access services at:

```
Backend API:        http://localhost:8000
API Documentation:  http://localhost:8000/docs
ReDoc:             http://localhost:8000/redoc
Health Check:      http://localhost:8000/health

Frontend UI:        http://localhost:5173

Database:          localhost:5432 (postgres:postgres)
Redis:             localhost:6379
Phoenix Dashboard: http://localhost:6006
```

## 📝 Environment Configuration

The `.env` file controls all settings:

```bash
# Application
APP_ENV=development
LOG_LEVEL=INFO
TRANSFORMATION_APPROACH=hybrid

# Database (uses Podman service names)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/iso_mapper
REDIS_URL=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Azure OpenAI (optional, for LLM features)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4-mini
```

## 🏗️ Architecture

### Backend (FastAPI)
- **Location:** `app/v4_refactored/`
- **Language:** Python 3.11
- **Framework:** FastAPI with async/await
- **Key Files:**
  - `api/main.py` - FastAPI app initialization
  - `api/routers/` - API endpoints (health, transform)
  - `api/schemas/` - Request/response models
  - `services/` - Business logic layer
  - `agents/` - LangGraph agents
  - `config/settings.py` - Configuration management
  - `shared/logger.py` - Structured logging

### Frontend (React)
- **Location:** `ui/`
- **Language:** TypeScript + React 18
- **Build Tool:** Vite
- **Key Files:**
  - `src/pages/` - Page components (Transform, Samples, Analytics)
  - `src/components/` - Reusable UI components
  - `src/services/api.ts` - API client
  - `src/store/` - Zustand state management
  - `src/types/` - TypeScript interfaces

### Services

| Service | Purpose | Port |
|---------|---------|------|
| **backend** | FastAPI application | 8000 |
| **frontend** | React UI | 5173 |
| **postgres** | PostgreSQL database | 5432 |
| **redis** | Redis cache | 6379 |
| **phoenix** | Observability dashboard | 6006 |

## 📦 Dependencies Overview

### Backend Core
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **SQLAlchemy** - ORM
- **AsyncPG** - PostgreSQL driver
- **LangGraph** - AI agent orchestration
- **LangChain** - AI tools and utilities
- **Azure OpenAI** - LLM integration

### Frontend Core
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client
- **React Router** - Navigation

See full lists in:
- Backend: `app/v4_refactored/requirements.txt`
- Frontend: `ui/package.json`

## 🔧 Development Workflow

### Backend Changes
1. Edit files in `app/v4_refactored/`
2. Changes auto-reload via uvicorn
3. Check logs: `make logs-backend`

### Frontend Changes
1. Edit files in `ui/src/`
2. Vite hot-reload updates automatically
3. View at http://localhost:5173

### Database Changes
1. Modify models in `app/v4_refactored/db/models.py`
2. Create migrations as needed
3. Check PostgreSQL: `make db-shell`

## 🧪 Testing

```bash
# Backend tests
podman-compose exec backend pytest tests/ -v

# Frontend tests
podman-compose exec frontend npm test

# Type checking
podman-compose exec backend mypy app/
podman-compose exec frontend npm run type-check
```

## 📋 Common Tasks

### View Application Logs
```bash
make logs              # All services
make logs-backend      # Backend only
make logs-frontend     # Frontend only
```

### Access Services
```bash
make backend-shell     # Python shell in backend
make frontend-shell    # Node shell in frontend
make db-shell          # PostgreSQL console
make redis-cli         # Redis CLI
```

### Restart Services
```bash
podman-compose restart backend
podman-compose restart frontend
```

### Rebuild Everything
```bash
make clean             # Remove all
make build             # Rebuild
make up                # Start again
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
make logs

# Verify Podman is running
podman ps

# Rebuild and restart
make clean && make build && make up
```

### Port already in use
Edit `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8001:8000"  # Use 8001 instead of 8000
```

### Database connection errors
```bash
# Check database is ready
podman-compose exec postgres pg_isready -U postgres

# Check environment variables
podman-compose exec backend env | grep DATABASE_URL
```

### Out of memory
```bash
# Increase Podman VM memory (macOS)
podman machine set --memory 4096

# Check current settings
podman info | grep -A5 "host:"
```

## 🚀 Production Deployment

For production, the application includes:
- ✓ Health check endpoints
- ✓ Structured JSON logging
- ✓ Performance tracing
- ✓ Error handling
- ✓ CORS configuration
- ✓ Environment-based settings

Deployment options:
- **Podman Pods** - Native Podman orchestration
- **Kubernetes** - Full container orchestration
- **Docker Compose** - Traditional deployment
- **Azure Container Instances** - Cloud deployment

See `app/v4_refactored/README.md` for detailed deployment guides.

## 📚 Documentation

- **Backend:** `app/v4_refactored/README.md`
- **Frontend:** `ui/README.md`
- **Refactoring Strategy:** `ISO_REFACTORING_STRATEGY.md`
- **Implementation Summary:** `IMPLEMENTATION_SUMMARY.md`
- **Podman Setup Guide:** `PODMAN_SETUP.md`

## 🔗 Useful Links

- [Podman Documentation](https://podman.io/docs)
- [podman-compose](https://github.com/containers/podman-compose)
- [FastAPI](https://fastapi.tiangolo.com)
- [React](https://react.dev)
- [Vite](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)

## 📞 Getting Help

1. Check logs: `make logs`
2. See API docs: http://localhost:8000/docs
3. Check configuration: Review `.env` file
4. Read documentation in `app/v4_refactored/README.md` and `ui/README.md`

## ✅ Next Steps

1. ✓ Run setup: `./podman-setup.sh` or `podman-setup.bat`
2. ✓ Access frontend: http://localhost:5173
3. → Explore transformation page
4. → Test API at http://localhost:8000/docs
5. → Implement business logic in backend
6. → Add tests and documentation
7. → Deploy to production

---

**Questions?** See the individual README files or documentation in the project root.
