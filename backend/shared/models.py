"""Shared Pydantic models for all services"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Chat Models
# ============================================================================

class Message(BaseModel):
    """Chat message"""
    role: Literal["user", "assistant", "system"]
    content: str


class Citation(BaseModel):
    """Source citation"""
    id: int
    title: str
    url: str
    source: str


class ChatRequest(BaseModel):
    """Request to /chat endpoint"""
    messages: List[Message]


class ChatResponse(BaseModel):
    """Response from /chat endpoint"""
    answer: str
    citations: List[Citation]
    triage: Literal["primary-care", "ER", "911"]
    red_flags: List[str]
    latency_ms: Optional[int] = None


# ============================================================================
# RAG Models
# ============================================================================

class Document(BaseModel):
    """Document for ingestion"""
    text: str
    title: str
    url: str
    source: str
    section: Optional[str] = "main"


class IngestRequest(BaseModel):
    """Request to /ingest endpoint"""
    documents: List[Document]


class IngestResponse(BaseModel):
    """Response from /ingest endpoint"""
    ingested_count: int
    chunk_count: int


class Chunk(BaseModel):
    """Text chunk with metadata"""
    text: str
    chunk_id: int
    metadata: dict


class RetrievalRequest(BaseModel):
    """Request to /retrieve endpoint"""
    query: str
    k: int = Field(default=8, ge=1, le=50)
    rerank_top_n: int = Field(default=3, ge=1, le=20)


class RetrievedDocument(BaseModel):
    """Retrieved document chunk"""
    doc_id: str
    text: str
    url: str
    source: str
    title: str
    chunk_id: int
    score: float


class RetrievalResponse(BaseModel):
    """Response from /retrieve endpoint"""
    hits: List[RetrievedDocument]
    latency_ms: int


# ============================================================================
# Orchestrator Models
# ============================================================================

class PatientFeatures(BaseModel):
    """Extracted patient features"""
    age: Optional[int] = None
    sex: Optional[str] = None
    duration_days: Optional[int] = None
    fever_c: Optional[float] = None
    symptoms_list: List[str] = []
    meds: List[str] = []
    query_terms: List[str] = []


class RedFlagCheck(BaseModel):
    """Red flag detection result"""
    er_required: bool
    red_flags: List[str]
    er_message: Optional[str] = None


class OrchestratorState(BaseModel):
    """LangGraph state"""
    messages: List[Message]
    features: Optional[PatientFeatures] = None
    red_flag_check: Optional[RedFlagCheck] = None
    retrieved_docs: List[RetrievedDocument] = []
    context_text: Optional[str] = None
    citations: List[Citation] = []
    answer: Optional[str] = None
    triage: str = "primary-care"
    trace_id: Optional[str] = None


# ============================================================================
# Health Check Models
# ============================================================================

class ServiceHealth(BaseModel):
    """Health status of a service"""
    name: str
    status: Literal["healthy", "unhealthy", "unknown"]
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response from /health endpoint"""
    status: Literal["healthy", "degraded", "unhealthy"]
    services: List[ServiceHealth]
