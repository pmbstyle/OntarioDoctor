# OntarioDoctor Backend

Backend services for the OntarioDoctor medical symptom-checker application.

## Services

### Gateway (Port 8000)
- **Purpose**: Public-facing API
- **Endpoints**: `/chat`, `/ingest`, `/health`
- **Dependencies**: Orchestrator, RAG

### Orchestrator (Port 8002)
- **Purpose**: LangGraph workflow coordination
- **Features**: Red-flag detection, symptom NLU, context assembly
- **Dependencies**: RAG, vLLM

### RAG (Port 8001)
- **Purpose**: Hybrid retrieval service
- **Features**: Vector search (Qdrant), BM25, cross-encoder reranking
- **Dependencies**: Qdrant

### vLLM (Port 8000)
- **Purpose**: LLM inference server
- **Model**: google/medgemma-4b-it
- **API**: OpenAI-compatible

## Setup

### 1. Create Virtual Environment

```bash
cd backend
chmod +x setup_venv.sh
./setup_venv.sh
```

This script will:
- Detect CUDA availability
- Install PyTorch with GPU support (if available) or CPU-only
- Install all dependencies from requirements.txt

### 2. Activate Environment

```bash
source venv/bin/activate
```

### 3. Verify Installation

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Project Structure

```
backend/
├── gateway/           # FastAPI public API
├── orchestrator/      # LangGraph workflow
│   └── nodes/         # Graph nodes
├── rag/              # Retrieval service
├── llm/              # vLLM configuration
├── shared/           # Shared models and utilities
│   ├── models.py     # Pydantic models
│   ├── constants.py  # Constants (Ontario-specific)
│   └── utils.py      # Utility functions
└── requirements.txt
```

## Environment Variables

See `.env.example` in project root for required configuration.

## Development

Each service can be run independently for development:

```bash
# Gateway
cd gateway && uvicorn main:app --reload --port 8000

# Orchestrator
cd orchestrator && uvicorn main:app --reload --port 8002

# RAG
cd rag && uvicorn main:app --reload --port 8001
```

## Docker

For production deployment, use Docker Compose from project root:

```bash
docker-compose up -d
```
