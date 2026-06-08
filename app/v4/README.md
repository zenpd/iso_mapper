# 🔄 ISO 20022 GenAI Migration Platform

A production-grade, LangGraph-powered MT to MX transformation system with Azure OpenAI integration.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-Powered-purple.svg)

## ✨ Features

- **🤖 LangGraph Agent Pipeline**: Parser → Mapping → Enrichment → Validation
- **🧠 Azure OpenAI Integration**: GPT-4o semantic understanding
- **⚡ Three Approaches**: Rule-based, LLM, Hybrid (configurable)
- **🎨 Beautiful Streamlit UI**: Real-time transformation visualization
- **🔧 Extensible Architecture**: Easy to add new agents

## 🏗️ Architecture

```
MT103 Input → Parser → Mapping → Enrichment → Validation → pacs.008 XML
                ↓         ↓          ↓            ↓
           Extract    Rule/LLM    Add LEI     Schema Check
            Fields      Map       BIC/Reg      Compliance
```

## 📁 Project Structure

```
mt_mx_platform/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration (pydantic-settings)
│   ├── models/schemas.py    # Pydantic models
│   ├── agents/              # All transformation agents
│   │   ├── base.py          # Base agent class
│   │   ├── parser.py        # MT Parser
│   │   ├── mapping.py       # Field mapping (rule/LLM)
│   │   ├── enrichment.py    # Data enrichment
│   │   └── validation.py    # Schema validation
│   ├── graph/workflow.py    # LangGraph workflow
│   └── services/llm_service.py  # Azure OpenAI
├── ui/streamlit_app.py      # Streamlit frontend
├── .env.example             # Environment template
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI

```bash
cp .env.example .env
# Edit .env with your credentials
```

```properties
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_API_KEY="your-api-key"
CHAT_LLM_DEPLOYMENT="your-deployment-name"
CHAT_LLM_MODEL="gpt-4o"
AZURE_API_VERSION="2024-02-15-preview"
```

> Works without Azure OpenAI (simulated mode) for testing.

### 3. Run Application

**Terminal 1 - API:**
```bash
uvicorn main:app --reload --port 8000
```

**Terminal 2 - UI:**
```bash
streamlit run streamlit_app.py --server.port 8501
```

### 4. Access

- **UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

## 🔧 Transformation Approaches

| Approach | Speed | Confidence | Best For |
|----------|-------|------------|----------|
| `rules` | ~50ms | 98%+ | Standard messages |
| `llm` | ~500ms | 90-95% | Complex scenarios |
| `hybrid` | ~200ms | 95-98% | Production (recommended) |

## 📡 API Usage

### Transform Message

```bash
POST /transform
{
  "mt_message": ":20:TRX001\n:32A:241118USD50000,00\n...",
  "approach": "hybrid"
}
```

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:8000/transform",
    json={
        "mt_message": ":20:TRX001\n:32A:241118USD50000,00\n:50K:/123\nACME\n:59:/456\nGLOBAL\n:71A:SHA",
        "approach": "hybrid"
    }
)

result = response.json()
print(f"Confidence: {result['statistics']['overall_confidence']*100:.1f}%")
```

## 🤖 Agent Details

| Agent | Function | Method |
|-------|----------|--------|
| **Parser** | Extract MT fields | Regex parsing |
| **Mapping** | MT→MX field mapping | Rules + LLM |
| **Enrichment** | Add regulatory fields | Knowledge graph + LLM |
| **Validation** | Schema compliance | Rules + LLM context |

## 🔒 Extensibility

### Add New Agent

```python
from app.agents.base import BaseAgent
from app.models.schemas import GraphState

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("Custom")
    
    async def process(self, state: GraphState) -> GraphState:
        # Your logic
        return state
```

### Add Custom Mapping Rules

```python
# In app/agents/mapping.py
self.rule_mappings["new_field"] = {
    "mx_path": "CdtTrfTxInf.Custom.Path",
    "confidence": 0.95,
    "reasoning": "Custom rule"
}
```

## 📊 Output Statistics

```json
{
  "statistics": {
    "total_duration_ms": 245,
    "fields_parsed": 8,
    "fields_mapped": 8,
    "fields_enriched": 6,
    "overall_confidence": 0.96,
    "validation_score": 100,
    "llm_inferences": 2
  }
}
```

## 🛡️ Production Checklist

- [ ] Configure Azure OpenAI credentials
- [ ] Add API authentication
- [ ] Implement rate limiting
- [ ] Add structured logging
- [ ] Set up monitoring/alerting
- [ ] Configure caching for LLM responses

## 📝 Supported Messages

| MT Type | MX Type | Description |
|---------|---------|-------------|
| MT103 | pacs.008 | Customer Credit Transfer |
| MT202 | pacs.009 | FI Credit Transfer |

## 📄 License

MIT License

---

**Built with LangGraph, Azure OpenAI, FastAPI & Streamlit**
