# OntarioDoctor (PoC)

A PoC of a medical symptom-checker chat application for Ontario residents, powered by RAG (Retrieval-Augmented Generation) with MedGemma-4b-it LLM.

<p align="center">
<img src="https://github.com/user-attachments/assets/cf137d01-f53e-4090-8e2b-60763c62f075" />
</p>

## 🎯 Features

- **💬 Conversational Interface**: Natural language symptom checking
- **📚 Grounded Responses**: All answers backed by medical sources with citations
- **🚨 Red-Flag Detection**: Automatic triage for emergency situations
- **🍁 Ontario-Focused**: Localized resources (Telehealth Ontario, walk-in clinics, ER guidance)
- **🔒 Privacy-First**: Session-based only, no data persistence or user accounts
- **⚡ Hybrid RAG**: Vector search + BM25 with cross-encoder reranking
- **🎨 Modern UI**: Vue 3 + TailwindCSS + shadcn-vue

## 🏗️ Architecture

```
┌─────────────┐
│  Frontend   │  Vue 3 + Pinia + TailwindCSS
│  (Port 5173)│
└──────┬──────┘
       │
       v
┌─────────────┐
│  Gateway    │  FastAPI (Port 8080)
│  /chat      │  Public API
│  /ingest    │
└──────┬──────┘
       │
       v
┌─────────────┐
│Orchestrator │  LangGraph (Port 8002)
│  Workflow   │  symptom_nlu → guardrails → retrieve → generate
└──────┬──────┘
       │
       ├──────> RAG Service (Port 8001)
       │        Qdrant + BM25 + Reranker
       │
       └──────> Ollama (Port 11434)
                MedGemma-4B-IT:Q6
```

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose**
- **NVIDIA GPU** with CUDA support (for Ollama)
- **Python 3.11+** (for local development)
- **Node 20+** & **pnpm** (for frontend development)

### 1. Clone Repository

```bash
git clone https://github.com/pmbstyle/OntarioDoctor.git
cd OntarioDoctor
```

### 2. Start All Services

```bash
make up
```

This will start:
- ✅ Qdrant (vector database)
- ✅ Ollama (LLM inference)
- ✅ RAG Service
- ✅ Orchestrator
- ✅ API Gateway
- ✅ Frontend

### 3. Ingest Sample Data

```bash
make ingest-sample
```

### 4. Access the App

Open your browser to **http://localhost:5173**

### 5. Run Smoke Tests

```bash
make smoke-test
```

## 📦 Project Structure

```
OntarioDoctor/
├── backend/
│   ├── gateway/          # FastAPI: /chat, /ingest, /health
│   ├── orchestrator/     # LangGraph workflow
│   ├── rag/             # Hybrid retrieval service
│   └── shared/          # Common models & utilities
├── frontend/            # Vue 3 chat interface
├── docs/                # Documentation
├── scripts/             # Sample data & tests
├── docker-compose.yml   # Service orchestration
├── Makefile            # Helper commands
└── README.md
```

## 🛠️ Development

### Backend (Local)

1. **Setup virtual environment:**
   ```bash
   make venv
   cd backend && source venv/bin/activate
   ```

2. **Run services individually:**
   ```bash
   # Terminal 1: RAG
   python -m uvicorn backend.rag.main:app --reload --port 8001

   # Terminal 2: Orchestrator
   python -m uvicorn backend.orchestrator.main:app --reload --port 8002

   # Terminal 3: Gateway
   python -m uvicorn backend.gateway.main:app --reload --port 8000
   ```

3. **Start Ollama** (if not using Docker):
   ```bash
   docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
   docker exec -it ollama ollama pull amsaravi/medgemma-4b-it:q6
   ```

### Frontend (Local)

```bash
cd frontend
pnpm install
pnpm dev
```

Access at **http://localhost:5173**

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `CUDA_VISIBLE_DEVICES`: GPU device ID (default: 0)
- `VITE_API_URL`: API Gateway URL for frontend
- `GATEWAY_CORS_ORIGINS`: Allowed CORS origins
- `*_LOG_LEVEL`: Logging levels (DEBUG, INFO, WARNING, ERROR)
