# ISO 20022 GenAI Migration Platform v3 (Refactored)

## Overview

This is the refactored edition of the ISO 20022 GenAI Migration Platform, restructured to follow **PayOrch architecture standards** for enterprise-grade applications.

**Key Improvements:**
- ✅ Modular layered architecture (API → Services → Business Logic)
- ✅ Structured JSON logging compatible with observability platforms
- ✅ Environment-scoped configuration with Pydantic settings
- ✅ Proper folder structure and separation of concerns
- ✅ LangGraph agents for AI-powered transformation
- ✅ FastAPI with async/await patterns
- ✅ Type hints throughout codebase
- ✅ Comprehensive error handling

## Architecture

```
api/                 # FastAPI layer
├── main.py          # App entry point with lifespan
├── routers/         # Modular endpoint definitions
├── schemas/         # Request/response Pydantic models
└── dependencies.py  # Dependency injection

services/            # Business logic layer
├── transformation.py    # Orchestration
├── mt_parser.py        # MT parsing
├── mx_generator.py     # MX generation
├── enrichment.py       # Field enrichment
└── validation.py       # Compliance checking

agents/              # LangGraph agents
├── mapping_agent.py      # MT→MX mapping
├── enrichment_agent.py   # Data enrichment
├── validation_agent.py   # Compliance validation
└── state.py              # Agent state definition

workflows/           # Workflow orchestration
└── mt_mx_transformation.py  # Main pipeline graph

config/              # Configuration
└── settings.py      # Pydantic BaseSettings

shared/              # Shared utilities
├── logger.py        # Structured JSON logging
└── exceptions.py    # Custom exceptions

observability/       # Monitoring & tracing
└── tracing.py       # Phoenix integration ready
```

## Quick Start

### Prerequisites
- Python 3.11+
- Poetry or pip
- Docker (optional)

### Local Development (No Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env

# Run backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### With Docker Compose

```bash
docker-compose up --build
```

## API Endpoints

### Health & Config
- `GET /` - Service info
- `GET /health` - Health check
- `GET /config` - Current configuration

### Transformation
- `POST /api/v1/transform` - Transform MT to MX
- `GET /api/v1/samples` - Get sample messages

## Configuration

Configuration is managed via environment variables (`.env` file or system env).

**Key Settings:**
- `APP_ENV` - Environment (development/production)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `TRANSFORMATION_APPROACH` - Strategy: `rules`, `llm`, or `hybrid`
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint (optional)
- `AZURE_API_KEY` - Azure API key (optional)
- `CORS_ALLOWED_ORIGINS` - Comma-separated CORS origins

See `.env.example` for all available settings.

## Transformation Pipeline

```
Raw SWIFT MT Message
         ↓
    [Parser] - Extracts fields
         ↓
[Mapping Agent] - Maps MT→MX schema
         ↓
[Enrichment Agent] - Adds mandatory fields
         ↓
[Validation Agent] - Checks compliance
         ↓
  [MX Generator] - Creates XML
         ↓
ISO 20022 MX XML + Statistics
```

## Development

### Coding Standards

- **Type Hints**: Full type annotations on all functions
- **Logging**: Structured JSON logging with context
- **Async**: Use async/await for I/O operations
- **Error Handling**: Custom exceptions with proper HTTP status codes
- **Testing**: Comprehensive unit and integration tests (to be added)

### Project Structure Rules

1. **API Layer** (`api/`): Request/response handling, routing, validation
2. **Service Layer** (`services/`): Business logic, orchestration
3. **Agent Layer** (`agents/`): LangGraph agents, workflow coordination
4. **Config Layer** (`config/`): Environment-based settings
5. **Shared Layer** (`shared/`): Utilities, logging, exceptions
6. **Observability** (`observability/`): Monitoring, tracing

### Adding New Endpoints

1. Create router in `api/routers/`
2. Define schemas in `api/schemas/`
3. Implement business logic in `services/`
4. Register router in `api/main.py`

Example:
```python
# api/routers/my_feature.py
from fastapi import APIRouter
from api.schemas import MyRequest, MyResponse

router = APIRouter(prefix="/api/v1", tags=["MyFeature"])

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest) -> MyResponse:
    # Implementation
    return response
```

## Next Steps

### Immediate (Phase 2-3)
- [ ] Implement actual MT parsing logic
- [ ] Integrate LangGraph agents
- [ ] Implement MX generation
- [ ] Add validation logic

### Short Term (Phase 4)
- [ ] Create React frontend (separate UI/ folder)
- [ ] Setup TypeScript + Vite + Tailwind
- [ ] Migrate from Streamlit

### Medium Term (Phase 5)
- [ ] Add database persistence (SQLAlchemy)
- [ ] Implement comprehensive testing
- [ ] Add Phoenix observability integration
- [ ] Performance optimization

### Long Term
- [ ] Production deployment guides
- [ ] Advanced caching strategies
- [ ] Real LLM integration (Azure OpenAI)
- [ ] Multi-tenant support

## Testing

```bash
# Run tests (when available)
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment guide.

## API Documentation

Automatic OpenAPI documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Module Import Errors
```bash
# Ensure you're in correct directory and app is in Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/app"
```

### LLM Not Configured
The app works with or without LLM. If you don't have Azure OpenAI configured,
set `TRANSFORMATION_APPROACH=rules` to use rule-based transformation only.

## References

- **PayOrch Reference**: See ../../../ for PayOrch application
- **FastAPI**: https://fastapi.tiangolo.com/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Pydantic**: https://docs.pydantic.dev/

## License

See LICENSE file in repository root.
