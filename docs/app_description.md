# 0) Objectives & Scope

**Goal:** A symptom-checker chat app that uses **RAG** with **vLLM (MedGemma-4b-it)**, returns grounded answers with citations, red-flag triage, and optional **Ontario (CA-ON)** localization (family doctor, walk-in clinic, Telehealth Ontario, etc.).

**Non-goals (for now):** PHI storage, user accounts, payments, HIPAA/PIPEDA compliance.

---

# 1) High-Level Architecture

```
Frontend (Vue/Electron/Web)
   |
   v
API Gateway (FastAPI): /chat, /intake, /health, /metrics
   |
   v
Orchestrator (LangGraph): router → symptom_nlu → retrieve → rerank → guardrails → assemble → generate → regionalize → log/eval
   |                                   |
   |                                   v
   |                              RAG Service (FastAPI)
   |                                - hybrid retriever (BM25 + Vector)
   |                                - cross-encoder reranker
   |                                - corpus versioning & filters
   |
   v
LLM Service (vLLM) → MedGemma-4b-it (OpenAI-compatible endpoint)
   |
   v
Observability: Langfuse/Langsmith + OpenTelemetry + Prometheus/Grafana

Data Plane:
  - Ingest Service (FastAPI/worker): fetch → normalize → chunk → embed → upsert
  - Vector DB (Qdrant or pgvector)
  - Keyword Index (Tantivy or OpenSearch)
  - Metadata Store (Postgres) for corpus versions, doc metadata, tenants, regions
```

---

# 2) Services & Repos

```
/backend
  /gateway           # FastAPI (public): /chat, /intake, /health, /metrics
  /orchestrator      # LangGraph flows, prompts, tools, policies
  /rag               # FastAPI (internal): /retrieve, /ingest, /corpus/version
  /ingest            # Ingestion jobs/parsers/chunkers/embeddings
  /llm               # vLLM runner/config (served separately)
  /eval              # Langfuse/Langsmith suites + datasets + scripts
  /infra             # Dockerfiles, docker-compose, Helm charts, k8s manifests
  /observability     # OTel collector, Prometheus rules, Grafana dashboards
README.md
```

---

# 3) Data Model (RAG)

**Vector store collection `docs`:**

* `id: string`
* `embedding: vector`
* `text: string` (chunk)
* `metadata: jsonb` with:

  * `source` (e.g., `medlineplus`, `dailymed`, `ontario.ca`)
  * `url`
  * `title`
  * `section`
  * `chunk_id: int`
  * `lang: "en"`
  * `tenant: ["global","CA-ON"]`
  * `version: "med-lite@2025.10.0"`
  * `pii: bool` (always false in POC)

**Keyword index fields (BM25):**

* `title`, `section`, `text`, `source`, `tenant`, `version`

**Corpus version registry (Postgres table `corpus_versions`):**

* `corpus_id`, `semver`, `created_at`, `notes`, `active: bool`

---

# 4) Ingestion Pipeline

**Sources (POC):**

* MedlinePlus topics (conditions, symptoms) → global
* DailyMed SPL (drug labels) → global
* A few curated Ontario pages (family doctor, walk-in clinic, doctor’s note) → `tenant=CA-ON`

**Steps:**

1. **Fetch** raw files (XML/HTML/MD/JSON).
2. **Normalize** → plain text + `title`, `section`, `url`, `source`, `tenant`, `lang`.
3. **Chunk**: target 700 tokens, overlap 120, cut on headings if available.
4. **Embed** (local): `BAAI/bge-small-en-v1.5` (normalize embeddings).
5. **Upsert** to Vector DB + Keyword Index.
6. **Register** new `version` (`med-lite@YYYY.MM.PATCH`).
7. **Smoke Eval** gates (hit-rate@k, faithfulness basic) before flipping `active=true`.

**Endpoints (internal):**

* `POST /rag/ingest` → trigger job with payload: `sources[], tenant[], version`
* `GET /rag/corpus/version` → list active versions

---

# 5) RAG Service (FastAPI)

**Responsibilities:**

* Hybrid retrieve: **ANN (vector)** ∪ **BM25** → score normalization/fusion
* Optional **rerank** with cross-encoder `bge-reranker-base`
* Filtering: `tenant`, `source`, `lang`, `version`
* Returns **top-N chunks** with metadata and a single `version` used

**API:**

```
POST /rag/retrieve
{
  "query": "fever 38.5 dry cough adult 2 days ibuprofen interactions",
  "k": 12,
  "filters": { "tenant": ["global","CA-ON"], "lang": "en", "sources": ["medlineplus","dailymed","ontario.ca"] },
  "rerank": { "top_n": 5 },
  "version": "med-lite@2025.10.0"     // optional; defaults to current active
}
→ 200
{
  "version": "med-lite@2025.10.0",
  "hits": [
    { "doc_id":"medlineplus:fever#17", "text":"...", "url":"...", "source":"medlineplus", "chunk_id":17, "score":0.83 },
    { "doc_id":"ontario:family-doctor#2","text":"...","url":"...","source":"ontario.ca","chunk_id":2,"score":0.78 }
  ],
  "trace_id":"rag-abc123",
  "latency_ms": 140
}
```

---

# 6) Orchestrator (LangGraph)

**Graph nodes (deterministic, retriable):**

1. `router` – detect if RAG needed (symptom Q → yes).
2. `symptom_nlu` – normalize input to **HPO** + extract structured features (age, sex, duration, fever, meds).

   * simple pattern rules + small LLM prompt if needed.
3. `retrieve_hybrid` – call `/rag/retrieve` with `query_terms` + filters (include `tenant` if region selected).
4. `rerank` – (optional) cross-encoder; keep top-M (e.g., 3–5).
5. `guardrails` – check **red flags** (chest pain + dyspnea, stiff neck + high fever, neuro deficits, anaphylaxis, etc.). If hit → short ER/911 path with citations.
6. `assemble_context` – dedupe, diversify by `source`, trim to token budget, label as `[1]..[N]`.
7. `generate_vllm` – call vLLM (OpenAI-compatible) with **system prompt** (below) and **user content** (context + patient features).
8. `regionalize_post` – rewrite CTAs and terms if `region=CA-ON` (family doctor, walk-in, Telehealth Ontario, OHIP).
9. `log_eval` – send Langfuse trace (inputs, retrieved docs, scores, output, red_flags), record timings.

**Pseudocode routing:**

```python
if has_red_flags(features or user_text):
    path = "er_advice"
else:
    path = "standard_rag_generation"
```

---

# 7) LLM Service (vLLM)

* Serve `google/medgemma-4b-it` behind OpenAI-compatible API.
* **Config**: `max_tokens`, `temperature=0.2`, `top_p=0.95`.
* **Endpoint**: `VLLM_BASE=/v1/chat/completions`.

**Gateway calls:**

```
POST {VLLM_BASE}/chat/completions
{
  "model": "medgemma-4b-it",
  "messages": [
    {"role":"system", "content": SYSTEM_PROMPT},
    {"role":"user", "content": USER_COMPOSED_CONTEXT_AND_QUESTION }
  ],
  "temperature": 0.2,
  "stream": false
}
```

---

# 8) Prompts

**SYSTEM_PROMPT (concise):**

```
You are a Canadian medical assistant.
Use ONLY the provided CONTEXT to answer.
Output in this structure:
1) Possible causes (3–5; not a diagnosis).
2) Red flags (if any).
3) What to do next in Canada (if region=CA-ON, prefer Ontario terms: family doctor, walk-in clinic, Telehealth Ontario).
4) Numbered citations [1]..[N].
Always append: “This is not medical advice.”
Be concise, clear, and avoid speculation beyond the sources.
```

**USER PROMPT TEMPLATE:**

```
CONTEXT:
[1] ({source}#{chunk_id}) {text}
[2] ...
...
PATIENT:
age={age}, sex={sex}, duration_days={duration_days}, fever_c={fever}, meds={meds}, region={region}
QUESTION:
{user_question}
```

---

# 9) API Gateway (FastAPI)

**/intake** – parse/normalize symptoms (optional separate call)

```
POST /intake
{
  "age": 10,
  "sex": "F",
  "symptoms_text": "fever 39, sore throat, 3 days",
  "meds": ["acetaminophen"],
  "region": "CA-ON"
}
→ 200 { "features": {...}, "hpo": ["HP:0001945", ...], "query_terms": ["fever","sore throat","child","3 days"] }
```

**/chat** – one-shot chat with embedded orchestration

```
POST /chat
{
  "messages": [{"role":"user","content":"My daughter has 39C fever and sore throat for 3 days. What to do?"}],
  "region": "CA-ON",
  "grounding": { "k": 8, "rerank_top_n": 3, "require_citations": true },
  "model": "medgemma-4b-it"
}
→ 200
{
  "triage": "primary-care_or_self-care | ER",
  "red_flags": [],
  "answer": " ... [1][2] ... This is not medical advice.",
  "citations": [
    {"id":1,"title":"Fever: self-care","url":"..."},
    {"id":2,"title":"Ontario: family doctor access","url":"..."}
  ],
  "trace_id":"run-abc123",
  "metrics": {"retrieve_ms":120,"rerank_ms":40,"generate_ms":610}
}
```

**/health, /metrics** – liveness and Prometheus metrics.

---

# 10) Guardrails (Red-Flag Rules)

Simple JSON rules + pattern matcher in `symptom_nlu`:

* Chest pain + shortness of breath → ER
* Stiff neck + high fever → ER
* Unilateral weakness/face droop/speech difficulty → ER
* Severe dehydration in child (no urination >8h, lethargy) → ER
* Anaphylaxis signs → ER

If triggered: skip standard generation and return short ER guidance with 1–2 citations.

---

# 11) Observability & Evaluation

* **Langfuse/Langsmith**: log inputs, retrieved chunks (ids, scores), output, latency per node.
* **Prometheus/Grafana**:

  * `retrieve_latency_ms`, `rerank_latency_ms`, `generate_latency_ms` (p50/p95)
  * `empty_retrieval_rate`, `cache_hit_rate`, `error_rate`
* **Eval suites** (`/eval`): 20–30 QA cases (adult/child fever, sore throat, ear pain, diarrhea, injury, drug interactions).

  * Offline metrics: hit-rate@k, answer relevancy, grounding/faithfulness (LLM-judge), red-flag routing correctness.

---

# 12) Configuration (ENV)

```
VLLM_BASE=http://llm:8000/v1
VLLM_MODEL=google/medgemma-4b-it
RAG_BASE=http://rag:8001
VECTOR_DB_URL=qdrant:6333
POSTGRES_URL=postgresql://...
KEYWORD_INDEX_URL=http://search:9200        # or embedded tantivy path
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
REGION_DEFAULT=global
ACTIVE_CORPUS=med-lite@2025.10.0
```

---

# 13) Local Run (Docker Compose)

Services:

* `gateway`, `orchestrator`, `rag`, `ingest`
* `vllm` (MedGemma), `qdrant` (or Postgres+pgvector), `search` (OpenSearch or tantivy sidecar)
* `langfuse`, `otel-collector`, `prometheus`, `grafana`

**Make targets:**

* `make up` – start stack
* `make ingest` – fetch/parse/chunk/embed/upsert; set `ACTIVE_CORPUS`
* `make smoke` – run a few curl tests
* `make eval` – run offline eval; print summary

---

# 14) Minimal Backlog (to impress interviewers)

1. End-to-end `/chat` with citations & red-flags.
2. Toggle `region=CA-ON` to show Canadian wording and Ontario routes.
3. Grafana dashboard with latency and empty-retrieval-rate.
4. Langfuse traces with retrieved docs and scores.
5. 20-case eval file + “release gate” (don’t activate new corpus if grounding < threshold).

---

# 15) Implementation Notes

* **Hybrid retrieval**: start with `k_dense=8` + `k_bm25=12` → fuse → rerank to top-3.
* **Chunk diversity**: prefer different sources in context, max 1–2 chunks per source.
* **Token budget**: aim total context ≤ 2k tokens for MedGemma; trim oldest/lowest-score chunks first.
* **Caching**: request cache by hash(query+filters+version) for 60–120s.
* **Regionalizer**: a small post-processor map (US→CA terms) + source-based CTA templates when `tenant=CA-ON`.
* **Safety**: always append “This is not medical advice.”

---

# 16) Example: Orchestrator (LangGraph) Node Signatures

* `router.run(messages) -> {"mode": "symptom_check"}`
* `symptom_nlu.run(messages) -> {"features": {...}, "hpo":[...], "query_terms":[...]}`
* `retrieve_hybrid.run(terms, region) -> { "hits":[...], "version": "..." }`
* `rerank.run(hits) -> { "hits":[top3] }`
* `guardrails.run(features, user_text) -> {"er": true|false, "reasons":[...] }`
* `assemble.run(hits) -> {"context_text": "...", "citations":[...]}`
* `generate_vllm.run(system, user) -> {"answer":"...", "raw":{...}}`
* `regionalize_post.run(answer, region) -> {"answer":"..."}`
* `log_eval.run(trace) -> {}`

---

That’s the blueprint. It’s clean, modular, and buzzword-correct for a JD: **FastAPI + LangGraph + RAG (hybrid + rerank) + vLLM + observability + eval + regionalization (CA-ON)**.

If you want, I can turn this into a `README.md` scaffold and a `docker-compose.yml` skeleton with stub endpoints you (or your LLM) can fill in.
