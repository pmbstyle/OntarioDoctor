# OntarioDoctor Implementation Strategy

## 🎯 Project Overview

**Goal**: Build a Canadian (Ontario-focused) medical symptom-checker with RAG-powered responses using MedGemma-4b-it, optimized for local deployment with GPU acceleration.

**Key Requirements**:
- Session-based chat with history (no user accounts)
- Always Ontario-focused (no region settings)
- RAG with hybrid retrieval (BM25 + vector)
- Red-flag triage for emergency situations
- Local deployment with Docker Compose
- CUDA GPU support with CPU fallback

---

## 📐 Architecture Decisions

### Simplifications from Original Design
- ✅ **Always Ontario**: Hardcode `tenant=CA-ON` everywhere, no region selection
- ✅ **Session-based only**: In-memory chat history per session (no persistence/auth)
- ✅ **Simple observability**: Python logging only (no Langfuse/Prometheus/Grafana)
- ✅ **Manual ingest**: `/ingest` endpoint for data upload (user provides prepared data)
- ✅ **Local-first**: Docker Compose with GPU passthrough for vLLM

### Technology Stack

**Backend:**
- **API Gateway**: FastAPI
- **Orchestrator**: LangGraph (state machine for RAG workflow)
- **RAG Service**: FastAPI + Qdrant + BM25
- **LLM**: vLLM serving MedGemma-4b-it
- **Embeddings**: `BAAI/bge-small-en-v1.5` (384-dim)
- **Reranker**: `BAAI/bge-reranker-base`
- **Vector DB**: Qdrant

**Frontend:**
- **Framework**: Vue 3 (Composition API)
- **State**: Pinia (session store)
- **Styling**: TailwindCSS + shadcn-vue
- **HTTP**: Axios

**Infrastructure:**
- **Deployment**: Docker Compose
- **GPU**: NVIDIA CUDA with CPU fallback

---

## 🏗️ Project Structure

```
OntarioDoctor/
├── backend/
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app with /chat, /ingest, /health
│   │   ├── config.py            # Environment config
│   │   └── dependencies.py      # Shared dependencies
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph state machine
│   │   ├── nodes/
│   │   │   ├── symptom_nlu.py   # Extract features, normalize symptoms
│   │   │   ├── guardrails.py    # Red-flag detection
│   │   │   ├── retrieve.py      # Call RAG service
│   │   │   ├── assemble.py      # Context assembly + citations
│   │   │   ├── generate.py      # Call vLLM
│   │   │   └── logger.py        # Logging node
│   │   ├── prompts.py           # System prompts (Ontario-specific)
│   │   └── rules.json           # Red-flag rules
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app with /retrieve, /ingest
│   │   ├── retriever.py         # Hybrid retrieval (vector + BM25)
│   │   ├── reranker.py          # Cross-encoder reranking
│   │   ├── embedder.py          # Embedding service
│   │   ├── chunker.py           # Text chunking logic
│   │   └── qdrant_client.py     # Qdrant connection wrapper
│   │
│   ├── llm/
│   │   ├── vllm_config.json     # vLLM server config
│   │   ├── run_vllm.sh          # Startup script with CUDA detection
│   │   └── requirements.txt     # vLLM-specific deps
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── models.py            # Pydantic models (ChatRequest, ChatResponse, etc.)
│   │   ├── utils.py             # Common utilities
│   │   └── constants.py         # Constants (tenant="CA-ON", etc.)
│   │
│   ├── requirements.txt         # Python dependencies
│   ├── setup_venv.sh            # venv setup with CUDA detection
│   └── README.md
│
├── frontend/                    # Existing Vue 3 boilerplate
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts        # Axios client for /chat
│   │   ├── components/
│   │   │   ├── ChatInterface.vue
│   │   │   ├── MessageBubble.vue
│   │   │   ├── CitationCard.vue
│   │   │   ├── RedFlagAlert.vue
│   │   │   └── InputBox.vue
│   │   ├── stores/
│   │   │   └── chatStore.ts     # Pinia: session history
│   │   ├── types/
│   │   │   └── chat.ts          # TypeScript types
│   │   └── views/
│   │       └── ChatView.vue     # Main chat page
│   └── ...
│
├── docker-compose.yml           # Full stack orchestration
├── Makefile                     # Helper commands
├── .env.example                 # Environment template
└── docs/
    ├── app_description.md       # Original architecture spec
    └── implementation_strategy.md  # This document
```

---

## 📝 Implementation Phases

### **Phase 1: Backend Foundation**
**Objective**: Set up project structure, Python environment, and shared models

**Tasks**:
1. Create directory structure: `backend/{gateway,orchestrator,rag,llm,shared}/`
2. Write `requirements.txt`:
   - `fastapi`, `uvicorn[standard]`
   - `langgraph`, `langchain`, `langchain-community`
   - `qdrant-client`
   - `sentence-transformers`, `transformers`, `torch`
   - `rank-bm25`
   - `openai` (for vLLM client)
   - `pydantic`, `pydantic-settings`
   - `httpx`, `python-multipart`
3. Create `setup_venv.sh`:
   - Detect CUDA availability with `nvidia-smi`
   - Install PyTorch with CUDA 12.1 if available, else CPU
   - Install all requirements
4. Define shared Pydantic models in `shared/models.py`:
   - `ChatRequest`, `ChatResponse`, `Message`, `Citation`
   - `IngestRequest`, `Document`, `RetrievalRequest`, `RetrievalResponse`
5. Create `shared/constants.py`:
   - `TENANT = "CA-ON"`
   - `EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"`
   - `RERANKER_MODEL = "BAAI/bge-reranker-base"`
   - `LLM_MODEL = "google/medgemma-4b-it"`

**Deliverables**:
- ✅ Complete directory structure
- ✅ Working Python venv with CUDA support
- ✅ Shared models and constants

---

### **Phase 2: RAG Service**
**Objective**: Build retrieval service with Qdrant + hybrid search

**Tasks**:
1. **Qdrant Setup** (`rag/qdrant_client.py`):
   - Initialize Qdrant client (local mode for dev)
   - Create collection `docs` with vector size 384
   - Define payload schema (text, title, url, source, section, chunk_id, tenant, lang)

2. **Embedding Service** (`rag/embedder.py`):
   - Load `BAAI/bge-small-en-v1.5`
   - Method: `embed(texts: List[str]) -> List[List[float]]`
   - Normalize embeddings (L2 norm)

3. **Chunking Logic** (`rag/chunker.py`):
   - Target 700 tokens per chunk, 120 token overlap
   - Method: `chunk_document(text: str, metadata: dict) -> List[Chunk]`

4. **Hybrid Retriever** (`rag/retriever.py`):
   - Vector search: Qdrant ANN (k=8)
   - BM25 search: In-memory index (k=12)
   - Score fusion: Reciprocal Rank Fusion (RRF)
   - Filter: Always `tenant=CA-ON`

5. **Reranker** (`rag/reranker.py`):
   - Load `BAAI/bge-reranker-base`
   - Method: `rerank(query: str, docs: List[Doc], top_n: int) -> List[Doc]`

6. **FastAPI Endpoints** (`rag/main.py`):
   - `POST /retrieve`:
     - Input: `{query, k, rerank_top_n}`
     - Output: `{hits: [{doc_id, text, url, source, chunk_id, score}], latency_ms}`
   - `POST /ingest`:
     - Input: `{documents: [{text, title, url, source, section}]}`
     - Process: chunk → embed → upsert to Qdrant + BM25 index
     - Output: `{ingested_count, chunk_count}`
   - `GET /health`: Return service status

**Deliverables**:
- ✅ Qdrant collection with schema
- ✅ Hybrid retrieval (vector + BM25)
- ✅ Cross-encoder reranking
- ✅ `/retrieve` and `/ingest` endpoints

---

### **Phase 3: LLM Service**
**Objective**: Set up vLLM with MedGemma-4b-it

**Tasks**:
1. **vLLM Configuration** (`llm/vllm_config.json`):
   ```json
   {
     "model": "google/medgemma-4b-it",
     "tensor_parallel_size": 1,
     "gpu_memory_utilization": 0.9,
     "max_model_len": 4096,
     "dtype": "auto"
   }
   ```

2. **Startup Script** (`llm/run_vllm.sh`):
   - Detect CUDA with `nvidia-smi`
   - Set `CUDA_VISIBLE_DEVICES` if GPU available
   - Run: `vllm serve google/medgemma-4b-it --port 8000 --host 0.0.0.0`
   - Fallback: CPU mode with reduced batch size

3. **Health Check**:
   - Endpoint: `http://llm:8000/health`
   - Test OpenAI-compatible API: `/v1/chat/completions`

**Deliverables**:
- ✅ vLLM server with MedGemma-4b-it
- ✅ CUDA detection + CPU fallback
- ✅ OpenAI-compatible API endpoint

---

### **Phase 4: Orchestrator**
**Objective**: Build LangGraph workflow with red-flag guardrails

**Tasks**:
1. **Red-Flag Rules** (`orchestrator/rules.json`):
   ```json
   {
     "er_rules": [
       {"symptoms": ["chest pain", "shortness of breath"], "action": "ER", "message": "Call 911 or go to ER immediately"},
       {"symptoms": ["stiff neck", "high fever"], "action": "ER", "message": "Go to ER immediately - possible meningitis"},
       {"symptoms": ["unilateral weakness", "face droop", "speech difficulty"], "action": "ER", "message": "Call 911 immediately - possible stroke"},
       {"symptoms": ["severe headache", "sudden", "worst ever"], "action": "ER", "message": "Go to ER immediately"},
       {"symptoms": ["anaphylaxis", "throat swelling", "difficulty breathing"], "action": "911", "message": "Call 911 immediately"}
     ]
   }
   ```

2. **System Prompt** (`orchestrator/prompts.py`):
   ```python
   SYSTEM_PROMPT = """You are a Canadian medical assistant for Ontario residents.
   Use ONLY the provided CONTEXT to answer.

   Output structure:
   1) Possible causes (3–5 conditions; NOT a diagnosis)
   2) Red flags (if any serious symptoms are present)
   3) What to do next in Ontario:
      - For non-urgent: See family doctor or walk-in clinic
      - For questions: Call Telehealth Ontario at 1-866-797-0000
      - For emergencies: Call 911 or go to ER
   4) Numbered citations [1]..[N] matching the CONTEXT sources

   Always append: "This is not medical advice. Call 911 for emergencies."
   Be concise, clear, and avoid speculation beyond the sources.
   """
   ```

3. **LangGraph Nodes**:

   **a) `symptom_nlu.py`** - Extract structured features:
   - Input: `messages: List[Message]`
   - Extract: age, sex, duration_days, fever_c, symptoms_list, meds
   - Output: `features: dict`, `query_terms: List[str]`

   **b) `guardrails.py`** - Check red flags:
   - Input: `features: dict`, `user_text: str`
   - Match against `rules.json` patterns
   - Output: `red_flags: List[str]`, `er_required: bool`, `er_message: str`

   **c) `retrieve.py`** - Call RAG service:
   - Input: `query_terms: List[str]`
   - HTTP POST to `http://rag:8001/retrieve`
   - Filters: `tenant=CA-ON`, `lang=en`
   - Output: `hits: List[Document]`

   **d) `assemble.py`** - Build context:
   - Input: `hits: List[Document]`
   - Deduplicate by `doc_id`, diversify sources
   - Label chunks as [1], [2], ..., [N]
   - Output: `context_text: str`, `citations: List[Citation]`

   **e) `generate.py`** - Call vLLM:
   - Input: `context_text: str`, `features: dict`, `user_question: str`
   - Build user prompt with CONTEXT + PATIENT + QUESTION
   - HTTP POST to `http://llm:8000/v1/chat/completions`
   - Config: `temperature=0.2`, `max_tokens=512`
   - Output: `answer: str`

   **f) `logger.py`** - Basic logging:
   - Log inputs, retrieved docs, red flags, response, latencies
   - Output: Log entry to stdout

4. **LangGraph State Machine** (`orchestrator/graph.py`):
   ```
   START → symptom_nlu → guardrails
                             ↓
                   [er_required?] ─Yes→ ER_PATH → END
                             ↓ No
                         retrieve → assemble → generate → logger → END
   ```

**Deliverables**:
- ✅ LangGraph workflow with 6 nodes
- ✅ Red-flag detection with ER routing
- ✅ Ontario-specific system prompt
- ✅ Context assembly with citations

---

### **Phase 5: Gateway API**
**Objective**: Public-facing FastAPI service

**Tasks**:
1. **Configuration** (`gateway/config.py`):
   - Load from environment:
     - `ORCHESTRATOR_URL` (default: `http://orchestrator:8002`)
     - `RAG_URL` (default: `http://rag:8001`)
     - `CORS_ORIGINS` (default: `["http://localhost:5173"]`)

2. **Endpoints** (`gateway/main.py`):

   **a) `POST /chat`**:
   - Input: `ChatRequest = {messages: List[Message]}`
   - Process: Forward to orchestrator → run LangGraph → return result
   - Output: `ChatResponse = {answer, citations, triage, red_flags, latency_ms}`

   **b) `POST /ingest`**:
   - Input: `IngestRequest = {documents: List[Document]}`
   - Process: Forward to `http://rag:8001/ingest`
   - Output: `{ingested_count, chunk_count}`

   **c) `GET /health`**:
   - Check: Gateway, Orchestrator, RAG, vLLM services
   - Output: `{status: "healthy|degraded", services: {...}}`

3. **CORS Middleware**:
   - Allow `http://localhost:5173` (frontend dev server)
   - Allow methods: GET, POST
   - Allow headers: Content-Type

**Deliverables**:
- ✅ `/chat` endpoint with orchestrator integration
- ✅ `/ingest` endpoint for data upload
- ✅ `/health` multi-service check
- ✅ CORS for frontend

---

### **Phase 6: Frontend Chat UI**
**Objective**: Vue 3 chat interface with session history

**Tasks**:
1. **TypeScript Types** (`frontend/src/types/chat.ts`):
   ```typescript
   interface Message {
     role: 'user' | 'assistant';
     content: string;
   }

   interface Citation {
     id: number;
     title: string;
     url: string;
     source: string;
   }

   interface ChatResponse {
     answer: string;
     citations: Citation[];
     triage: 'primary-care' | 'ER' | '911';
     red_flags: string[];
   }
   ```

2. **API Client** (`frontend/src/api/client.ts`):
   - Axios instance with base URL: `http://localhost:8000`
   - Method: `sendMessage(messages: Message[]) => Promise<ChatResponse>`

3. **Pinia Store** (`frontend/src/stores/chatStore.ts`):
   - State: `messages: Message[]`, `loading: boolean`, `error: string | null`
   - Actions: `sendMessage(content: string)`, `clearHistory()`

4. **Components**:

   **a) `ChatInterface.vue`** - Main layout:
   - Header: "OntarioDoctor - Ontario Medical Assistant"
   - Message list (scrollable)
   - Input box at bottom

   **b) `MessageBubble.vue`** - Message display:
   - User messages: Right-aligned, blue background
   - Assistant messages: Left-aligned, gray background
   - Markdown rendering with citations as links [1], [2], etc.

   **c) `CitationCard.vue`** - Citation display:
   - Show below assistant message
   - Format: `[1] Title - Source`
   - Clickable link to URL

   **d) `RedFlagAlert.vue`** - Warning banner:
   - Show when `triage = 'ER' | '911'`
   - Red background, urgent styling
   - Display red flag messages

   **e) `InputBox.vue`** - User input:
   - Textarea with auto-resize
   - Send button (disabled when loading)
   - Loading spinner

5. **Main View** (`frontend/src/views/ChatView.vue`):
   - Compose all components
   - Handle scroll to bottom on new messages

**Deliverables**:
- ✅ Pinia store with session history
- ✅ Chat interface with message bubbles
- ✅ Citation display with links
- ✅ Red-flag alert banner
- ✅ Responsive design with TailwindCSS

---

### **Phase 7: Docker Compose**
**Objective**: Full stack local deployment

**Tasks**:
1. **Services Configuration** (`docker-compose.yml`):

   **a) Qdrant**:
   ```yaml
   qdrant:
     image: qdrant/qdrant:latest
     ports: ["6333:6333"]
     volumes: ["./qdrant_data:/qdrant/storage"]
   ```

   **b) vLLM**:
   ```yaml
   vllm:
     build: ./backend/llm
     ports: ["8000:8000"]
     volumes: ["~/.cache/huggingface:/root/.cache/huggingface"]
     deploy:
       resources:
         reservations:
           devices:
             - driver: nvidia
               count: 1
               capabilities: [gpu]
   ```

   **c) RAG**:
   ```yaml
   rag:
     build: ./backend/rag
     ports: ["8001:8001"]
     environment:
       - QDRANT_URL=http://qdrant:6333
     depends_on: [qdrant]
   ```

   **d) Orchestrator**:
   ```yaml
   orchestrator:
     build: ./backend/orchestrator
     ports: ["8002:8002"]
     environment:
       - RAG_URL=http://rag:8001
       - VLLM_URL=http://vllm:8000
     depends_on: [rag, vllm]
   ```

   **e) Gateway**:
   ```yaml
   gateway:
     build: ./backend/gateway
     ports: ["8000:8000"]
     environment:
       - ORCHESTRATOR_URL=http://orchestrator:8002
       - RAG_URL=http://rag:8001
     depends_on: [orchestrator]
   ```

   **f) Frontend**:
   ```yaml
   frontend:
     build: ./frontend
     ports: ["5173:5173"]
     volumes: ["./frontend:/app", "/app/node_modules"]
     environment:
       - VITE_API_URL=http://localhost:8000
   ```

2. **Dockerfiles**:
   - `backend/gateway/Dockerfile`: Python 3.11 + FastAPI
   - `backend/orchestrator/Dockerfile`: Python 3.11 + LangGraph
   - `backend/rag/Dockerfile`: Python 3.11 + sentence-transformers
   - `backend/llm/Dockerfile`: vLLM base image + startup script
   - `frontend/Dockerfile`: Node 20 + Vite

3. **Makefile**:
   ```makefile
   up:
       docker-compose up -d

   down:
       docker-compose down

   logs:
       docker-compose logs -f

   ingest-sample:
       curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d @sample_data.json

   smoke-test:
       curl http://localhost:8000/health
       curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"I have a fever of 38.5C for 2 days"}]}'
   ```

4. **Environment Template** (`.env.example`):
   ```
   # GPU
   CUDA_VISIBLE_DEVICES=0

   # Service URLs
   GATEWAY_URL=http://localhost:8000
   QDRANT_URL=http://qdrant:6333

   # Models
   EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
   RERANKER_MODEL=BAAI/bge-reranker-base
   LLM_MODEL=google/medgemma-4b-it
   ```

**Deliverables**:
- ✅ Docker Compose with 6 services
- ✅ GPU passthrough for vLLM
- ✅ Volume mounts for persistence
- ✅ Makefile with helper commands

---

### **Phase 8: Integration & Testing**
**Objective**: End-to-end validation

**Tasks**:
1. **Sample Data** (`sample_data.json`):
   - 5-10 mock documents:
     - Fever: causes, when to see doctor, red flags
     - Sore throat: strep vs viral, treatment
     - Chest pain: urgent vs non-urgent
     - Ontario-specific: family doctor access, walk-in clinics, Telehealth Ontario

2. **Smoke Test Script** (`scripts/smoke_test.sh`):
   - Test `/health` → all services healthy
   - Test `/ingest` → upload sample data
   - Test `/retrieve` → query "fever" returns results
   - Test `/chat` → end-to-end with citations

3. **Manual E2E Test**:
   - Open `http://localhost:5173`
   - Send message: "My child has 39C fever for 3 days and sore throat"
   - Verify:
     - Assistant response with causes
     - Citations displayed with links
     - Ontario-specific advice (family doctor, Telehealth Ontario)
     - "This is not medical advice" disclaimer

4. **Performance Validation**:
   - `/chat` latency < 5s (cold start) or < 2s (warm)
   - Retrieval latency < 200ms
   - vLLM generation latency < 3s

**Deliverables**:
- ✅ Sample data for testing
- ✅ Automated smoke tests
- ✅ Manual E2E validation checklist
- ✅ Performance benchmarks

---

## 🔧 Technical Specifications

### **API Contracts**

#### **Gateway: POST /chat**
```json
// Request
{
  "messages": [
    {"role": "user", "content": "I have a fever of 38.5C for 2 days"}
  ]
}

// Response
{
  "answer": "Based on the provided information, here are possible causes... [1][2]",
  "citations": [
    {"id": 1, "title": "Fever in Adults", "url": "https://...", "source": "medlineplus"},
    {"id": 2, "title": "When to See a Doctor", "url": "https://...", "source": "ontario.ca"}
  ],
  "triage": "primary-care",
  "red_flags": [],
  "latency_ms": 1820
}
```

#### **Gateway: POST /ingest**
```json
// Request
{
  "documents": [
    {
      "text": "Full text of medical article...",
      "title": "Fever: Causes and Treatment",
      "url": "https://medlineplus.gov/fever.html",
      "source": "medlineplus",
      "section": "Overview"
    }
  ]
}

// Response
{
  "ingested_count": 1,
  "chunk_count": 5
}
```

#### **RAG: POST /retrieve**
```json
// Request
{
  "query": "fever 38.5 adult 2 days",
  "k": 8,
  "rerank_top_n": 3
}

// Response
{
  "hits": [
    {
      "doc_id": "medlineplus:fever#17",
      "text": "A fever is a body temperature above 38°C...",
      "url": "https://...",
      "source": "medlineplus",
      "chunk_id": 17,
      "score": 0.83
    }
  ],
  "latency_ms": 140
}
```

### **Prompt Engineering**

#### **System Prompt** (Ontario-specific)
```
You are a Canadian medical assistant for Ontario residents.
Use ONLY the provided CONTEXT to answer.

Output structure:
1) Possible causes (3–5 conditions; NOT a diagnosis)
2) Red flags (if any serious symptoms are present)
3) What to do next in Ontario:
   - For non-urgent: See family doctor or walk-in clinic
   - For questions: Call Telehealth Ontario at 1-866-797-0000
   - For emergencies: Call 911 or go to ER
4) Numbered citations [1]..[N] matching the CONTEXT sources

Always append: "This is not medical advice. Call 911 for emergencies."
Be concise, clear, and avoid speculation beyond the sources.
```

#### **User Prompt Template**
```
CONTEXT:
[1] (medlineplus#17) A fever is a body temperature above 38°C (100.4°F). It's usually a sign that your body is fighting an infection...
[2] (ontario.ca#2) If you need medical advice, you can call Telehealth Ontario at 1-866-797-0000...

PATIENT:
age=35, sex=M, duration_days=2, fever_c=38.5, meds=[], region=CA-ON

QUESTION:
I have a fever of 38.5C for 2 days
```

### **Red-Flag Rules** (JSON)
```json
{
  "er_rules": [
    {
      "symptoms": ["chest pain", "shortness of breath"],
      "action": "ER",
      "message": "Call 911 or go to ER immediately - possible heart attack"
    },
    {
      "symptoms": ["stiff neck", "high fever"],
      "action": "ER",
      "message": "Go to ER immediately - possible meningitis"
    },
    {
      "symptoms": ["unilateral weakness", "face droop", "speech difficulty"],
      "action": "ER",
      "message": "Call 911 immediately - possible stroke"
    },
    {
      "symptoms": ["severe headache", "sudden", "worst ever"],
      "action": "ER",
      "message": "Go to ER immediately - possible aneurysm"
    },
    {
      "symptoms": ["anaphylaxis", "throat swelling", "difficulty breathing"],
      "action": "911",
      "message": "Call 911 immediately - severe allergic reaction"
    },
    {
      "symptoms": ["severe dehydration", "no urination", "lethargy", "child"],
      "action": "ER",
      "message": "Go to ER immediately - severe dehydration in child"
    }
  ]
}
```

### **Vector DB Schema** (Qdrant)
```python
{
  "collection_name": "docs",
  "vector_size": 384,  # bge-small-en-v1.5
  "distance": "Cosine",
  "payload_schema": {
    "text": "str",        # Chunk content
    "title": "str",      # Document title
    "url": "str",        # Source URL
    "source": "str",     # e.g., "medlineplus", "ontario.ca"
    "section": "str",    # Document section
    "chunk_id": "int",   # Chunk index in document
    "tenant": "str",     # Always "CA-ON"
    "lang": "str"        # Always "en"
  }
}
```

---

## 🚀 Execution Order

1. ✅ **Phase 1**: Backend structure + venv setup
2. ✅ **Phase 2**: RAG service (Qdrant + hybrid retrieval)
3. ✅ **Phase 3**: vLLM setup (CUDA detection + runner)
4. ✅ **Phase 4**: Orchestrator (LangGraph nodes + guardrails)
5. ✅ **Phase 5**: Gateway API (FastAPI endpoints)
6. ✅ **Phase 6**: Frontend UI (Vue chat interface)
7. ✅ **Phase 7**: Docker Compose (full stack integration)
8. ✅ **Phase 8**: Smoke tests + documentation

---

## 📦 Deliverables Checklist

### Backend
- [ ] Python venv with CUDA support + CPU fallback
- [ ] Shared Pydantic models and constants
- [ ] RAG service with `/retrieve` and `/ingest` endpoints
- [ ] Hybrid retrieval (vector + BM25) with reranking
- [ ] vLLM server with MedGemma-4b-it
- [ ] LangGraph orchestrator with 6 nodes
- [ ] Red-flag guardrails with ER routing
- [ ] Gateway API with `/chat`, `/ingest`, `/health`

### Frontend
- [ ] Pinia store for session history
- [ ] Chat interface with message bubbles
- [ ] Citation cards with links
- [ ] Red-flag alert banner
- [ ] Responsive design with TailwindCSS

### Infrastructure
- [ ] Docker Compose with 6 services
- [ ] GPU passthrough for vLLM
- [ ] Makefile with helper commands
- [ ] Sample data for testing

### Testing
- [ ] Smoke test script
- [ ] Manual E2E validation
- [ ] Performance benchmarks

---

## 🔐 Security & Safety

### Data Safety
- ✅ No PHI storage (session-only, no persistence)
- ✅ No user accounts or authentication
- ✅ No logging of personal information

### Medical Safety
- ✅ Red-flag detection for emergencies
- ✅ Always append "This is not medical advice"
- ✅ Ontario-specific emergency contacts (911, Telehealth Ontario)
- ✅ Grounded responses with citations only

### Technical Safety
- ✅ CORS restrictions (localhost only)
- ✅ Input validation with Pydantic
- ✅ Rate limiting (future: if needed)

---

## 📈 Performance Targets

- **E2E Latency**: < 5s (cold start), < 2s (warm)
- **Retrieval**: < 200ms
- **vLLM Generation**: < 3s
- **Throughput**: 1 request/sec (single GPU)

---

## 🎯 Success Criteria

1. ✅ User can send message and receive grounded answer with citations
2. ✅ Red-flag symptoms trigger ER guidance
3. ✅ All responses include Ontario-specific advice
4. ✅ Chat history persists within session
5. ✅ Full stack runs locally with `make up`
6. ✅ Sample data ingestion works via `/ingest`
7. ✅ GPU acceleration works (if available)
8. ✅ CPU fallback works (if no GPU)

---

## 📚 References

- **Original Design**: `docs/app_description.md`
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **vLLM**: https://docs.vllm.ai/
- **Qdrant**: https://qdrant.tech/documentation/
- **MedGemma**: https://huggingface.co/google/medgemma-4b-it
- **BGE Models**: https://huggingface.co/BAAI

---

**Status**: Ready for implementation
**Last Updated**: 2025-10-28
