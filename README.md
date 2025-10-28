# OntarioDoctor 🇨🇦

A medical symptom-checker chat application for Ontario residents, powered by RAG (Retrieval-Augmented Generation) with MedGemma-4b-it LLM.

## 🎯 Features

- **💬 Conversational Interface**: Natural language symptom checking
- **📚 Grounded Responses**: All answers backed by medical sources with citations
- **🚨 Red-Flag Detection**: Automatic triage for emergency situations
- **🇨🇦 Ontario-Focused**: Localized resources (Telehealth Ontario, walk-in clinics, ER guidance)
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
       └──────> vLLM (Port 8000)
                MedGemma-4b-it
```

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose**
- **NVIDIA GPU** with CUDA support (for vLLM)
- **Python 3.11+** (for local development)
- **Node 20+** & **pnpm** (for frontend development)

### 1. Clone Repository

```bash
git clone <repo-url>
cd OntarioDoctor
```

### 2. Start All Services

```bash
make up
```

This will start:
- ✅ Qdrant (vector database)
- ✅ vLLM (LLM inference)
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
│   ├── llm/             # vLLM configuration
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

3. **Start vLLM:**
   ```bash
   cd backend/llm
   ./run_vllm.sh
   ```

### Frontend (Local)

```bash
cd frontend
pnpm install
pnpm dev
```

Access at **http://localhost:5173**

## 🧪 Testing

### Smoke Tests

```bash
make smoke-test
```

Tests:
- ✅ Service health checks
- ✅ Data ingestion
- ✅ RAG retrieval
- ✅ Chat endpoint
- ✅ Red-flag detection
- ✅ Frontend accessibility

### Health Checks

```bash
make health
```

## 📋 Makefile Commands

```bash
make help             # Show all commands
make up               # Start all services
make down             # Stop all services
make logs             # Show service logs
make restart          # Restart all services
make clean            # Clean up (remove volumes)
make venv             # Setup Python virtual environment
make ingest-sample    # Ingest sample medical data
make smoke-test       # Run smoke tests
make health           # Check service health
make quickstart       # Full setup + start
```

## 🔧 Configuration

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

## 🇨🇦 Ontario-Specific Features

- **Telehealth Ontario**: 1-866-797-0000 (24/7)
- **Emergency Number**: 911
- **Healthcare Options**: Family doctor, walk-in clinic, urgent care
- **Localized Advice**: All responses tailored for Ontario residents

## 🚨 Red-Flag Detection

Automatic triage for serious symptoms:
- Chest pain + shortness of breath → **ER**
- Stiff neck + high fever → **ER** (meningitis)
- Unilateral weakness/face droop → **911** (stroke)
- Severe headache (sudden) → **ER** (aneurysm)
- Anaphylaxis/throat swelling → **911**
- Infant fever (<3 months) → **ER**

## 📚 Tech Stack

### Backend
- **FastAPI**: Modern async Python web framework
- **LangGraph**: State machine for RAG workflow
- **Qdrant**: Vector database
- **vLLM**: Fast LLM inference (CUDA-accelerated)
- **sentence-transformers**: Embeddings (bge-small-en-v1.5)
- **rank-bm25**: Keyword search
- **Pydantic**: Data validation

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **Pinia**: State management
- **TailwindCSS**: Utility-first CSS
- **shadcn-vue**: UI components
- **TypeScript**: Type safety
- **Vite**: Build tool

### ML Models
- **LLM**: google/medgemma-4b-it (medical fine-tuned)
- **Embeddings**: BAAI/bge-small-en-v1.5 (384-dim)
- **Reranker**: BAAI/bge-reranker-base (cross-encoder)

## 📊 Service Ports

| Service      | Port | Description |
|--------------|------|-------------|
| Frontend     | 5173 | Vue 3 dev server |
| Gateway      | 8080 | Public API |
| Orchestrator | 8002 | Internal workflow |
| RAG          | 8001 | Retrieval service |
| vLLM         | 8000 | LLM inference |
| Qdrant       | 6333 | Vector DB |

## 🔐 Security & Safety

### Medical Safety
- ✅ Always appends "This is not medical advice"
- ✅ Red-flag detection for emergencies
- ✅ Grounded responses (citations required)
- ✅ Ontario-specific emergency numbers

### Data Safety
- ✅ No PHI storage
- ✅ Session-based only (no persistence)
- ✅ No user accounts or authentication
- ✅ CORS restrictions

## 📖 Documentation

- **Implementation Strategy**: `docs/implementation_strategy.md`
- **App Description**: `docs/app_description.md`
- **Backend README**: `backend/README.md`
- **Frontend README**: `frontend/README.md`

## 🐛 Troubleshooting

### vLLM won't start
- Ensure NVIDIA drivers installed: `nvidia-smi`
- Check CUDA version compatibility
- Verify GPU memory (needs ~8GB for MedGemma-4b)

### Frontend can't connect to backend
- Check gateway is running: `curl http://localhost:8080/health`
- Verify CORS settings in `.env`
- Check `VITE_API_URL` in `frontend/.env`

### RAG returns no results
- Ensure data ingested: `make ingest-sample`
- Check Qdrant health: `curl http://localhost:6333/health`
- Verify embeddings loaded

### Services won't start
- Check Docker logs: `make logs`
- Verify ports not in use: `lsof -i :8080`
- Ensure sufficient resources (16GB RAM recommended)

## 🤝 Contributing

This is a portfolio project. Feel free to fork and modify for your own use.

## ⚠️ Disclaimer

**This is not medical advice.** This application is a proof-of-concept symptom-checker tool and should not replace professional medical consultation.

For emergencies, always call **911**.
For medical advice, contact **Telehealth Ontario** at **1-866-797-0000**.

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

- Medical data sources: MedlinePlus, Ontario.ca
- LLM: Google MedGemma
- Embeddings: BAAI BGE models
- UI Components: shadcn-vue

---

**Built with ❤️ for Ontario residents**
