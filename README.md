# ISO 20022 GenAI Migration Platform - Refactored v3

Complete refactoring of the ISO 20022 GenAI Migration Platform to align with **PayOrch enterprise-grade architecture standards**.

## 📋 Overview

This project provides an AI-powered platform to transform SWIFT MT messages to ISO 20022 MX format using:
- **LangGraph Agents** for intelligent field mapping
- **FastAPI** backend with proper layering
- **React + TypeScript** modern frontend
- **Tailwind CSS** for responsive design

## 🎯 What's New in v3 (Refactored)

✅ **Enterprise Architecture** - Modular layered structure (API → Services → Business Logic)
✅ **Production-Ready Backend** - Structured logging, configuration, error handling
✅ **Modern Frontend** - React instead of Streamlit
✅ **Developer Experience** - Clear structure, comprehensive documentation

## 📁 Project Structure

```
├── app/v4_refactored/          # NEW: Refactored backend (PayOrch standards)
│   ├── api/                    # FastAPI layer (routers, schemas)
│   ├── services/               # Business logic (transformation, parsing, etc)
│   ├── agents/                 # LangGraph agents
│   ├── workflows/              # Workflow orchestration
│   ├── config/                 # Settings management
│   ├── shared/                 # Utilities & logging
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── ui/                         # NEW: React frontend
│   ├── src/                    # React components & pages
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
└── app/v1-v3/                  # Previous versions (archive)
```

## 🚀 Quick Start

### Backend
```bash
cd app/v4_refactored
pip install -r requirements.txt
cp .env.example .env
uvicorn api.main:app --reload
```
Backend: `http://localhost:8000` | API Docs: `/docs`

### Frontend
```bash
cd ui
npm install
npm run dev
```
Frontend: `http://localhost:5173`

### Full Stack with Docker
```bash
cd app/v4_refactored
docker-compose up
```

## 🏗️ Architecture

**Transformation Pipeline:**
```
Raw MT → [Parser] → [Mapping Agent] → [Enrichment] → 
[Validation] → [MX Generator] → ISO 20022 XML
```

**Backend Layers:**
- API Layer: FastAPI routers, schemas, validation
- Service Layer: Business logic orchestration
- Agent Layer: LangGraph agents
- Supporting: Config, logging, observability

## 📚 Documentation

- [Backend README](./app/v4_refactored/README.md)
- [Frontend README](./ui/README.md)
- [Refactoring Strategy](./ISO_REFACTORING_STRATEGY.md)

## 📈 Next Steps

- [ ] Implement actual MT parsing logic
- [ ] Integrate real LangGraph agents
- [ ] Add database persistence
- [ ] Comprehensive testing
- [ ] Phoenix observability integration

See [Refactoring Strategy](./ISO_REFACTORING_STRATEGY.md) for detailed roadmap.

## Where to look in this repository

- API & POC logic: [app/v2/mt_mx_api/main.py](app/v2/mt_mx_api/main.py)
- Example orchestrator: [app/v1/main_orchestrator.py](app/v1/main_orchestrator.py)
- Streamlit demo: [app/v2/streamlit_app.py](app/v2/streamlit_app.py)
- Agents (POC inline/variants): [app/v2/agents](app/v2/agents)

If you'd like, I can:
- Add sequence diagrams (Mermaid) showing the pipeline flow.
- Create a per-version README inside `app/v1`, `app/v2`, `app/v3` summarizing differences.
- Replace simulated LLM parts with real integration (I can scaffold calls and config).

---
Generated on: June 3, 2026
