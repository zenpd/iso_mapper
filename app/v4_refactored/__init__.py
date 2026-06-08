"""ISO 20022 GenAI Migration Platform v3 — Refactored Edition.

Refactored to follow PayOrch architecture standards:
- Modular layered architecture (API → Services → Business Logic)
- Structured JSON logging with Phoenix observability ready
- Proper configuration management with Pydantic settings
- LangGraph agents for AI-powered transformation
- FastAPI with async/await patterns
- TypeScript React frontend with Tailwind CSS (separate from backend)

Transformation Pipeline:
    Raw MT → [Parser] → [Mapping Agent] → [Enrichment Agent] → 
    [Validation Agent] → [MX Generator] → MX XML

See docs/ for architecture documentation.
"""
__version__ = "3.0.0"
__author__ = "Digital Banking Team"
__description__ = "Agentic MT to MX transformation platform"
