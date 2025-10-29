import time
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client.models import PointStruct

from backend.shared.models import (
    IngestRequest,
    IngestResponse,
    RetrievalRequest,
    RetrievalResponse,
    RetrievedDocument
)
from backend.shared.utils import setup_logging
from backend.shared.constants import TENANT, LANGUAGE
from backend.rag.config import settings
from backend.rag.qdrant_client import QdrantService
from backend.rag.embedder import EmbeddingService
from backend.rag.chunker import TextChunker
from backend.rag.retriever import HybridRetriever
from backend.rag.reranker import RerankerService


# Setup logging
logger = setup_logging("rag", level=getattr(__import__('logging'), settings.log_level))

# Initialize FastAPI app
app = FastAPI(title="RAG Service", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
qdrant_service = None
embedding_service = None
chunker = None
retriever = None
reranker = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global qdrant_service, embedding_service, chunker, retriever, reranker

    logger.info("Starting RAG service...")

    # Initialize services
    qdrant_service = QdrantService(url=settings.qdrant_url)
    embedding_service = EmbeddingService()
    chunker = TextChunker()
    retriever = HybridRetriever(qdrant_service, embedding_service)
    reranker = RerankerService()

    logger.info("RAG service started successfully")


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        count = qdrant_service.count()
        return {
            "status": "healthy",
            "service": "rag",
            "qdrant_connection": "ok",
            "documents_indexed": count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Ingest documents into the RAG system

    Workflow:
    1. Chunk documents
    2. Generate embeddings
    3. Upsert to Qdrant
    4. Update BM25 index
    """
    start_time = time.time()

    try:
        # 1. Chunk documents
        chunks = chunker.chunk_documents(request.documents)
        logger.info(f"Generated {len(chunks)} chunks from {len(request.documents)} documents")

        # 2. Generate embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = embedding_service.embed(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # 3. Prepare points for Qdrant
        points = []
        bm25_docs = []

        for chunk, embedding in zip(chunks, embeddings):
            # Generate unique doc_id
            doc_id = f"{chunk.metadata['source']}:{chunk.metadata['title']}#{chunk.chunk_id}"

            # Qdrant point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "doc_id": doc_id,
                    "text": chunk.text,
                    "title": chunk.metadata["title"],
                    "url": chunk.metadata["url"],
                    "source": chunk.metadata["source"],
                    "section": chunk.metadata["section"],
                    "chunk_id": chunk.chunk_id,
                    "tenant": TENANT,
                    "lang": LANGUAGE
                }
            )
            points.append(point)

            # BM25 doc
            bm25_doc = {
                "doc_id": doc_id,
                "text": chunk.text,
                "title": chunk.metadata["title"],
                "url": chunk.metadata["url"],
                "source": chunk.metadata["source"],
                "chunk_id": chunk.chunk_id,
                "tenant": TENANT,
                "lang": LANGUAGE
            }
            bm25_docs.append(bm25_doc)

        # 4. Upsert to Qdrant
        qdrant_service.upsert(points)

        # 5. Update BM25 index
        retriever.index_for_bm25(bm25_docs)

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Ingestion completed in {elapsed_ms}ms")

        return IngestResponse(
            ingested_count=len(request.documents),
            chunk_count=len(chunks)
        )

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve(request: RetrievalRequest):
    """
    Retrieve relevant documents for a query

    Workflow:
    1. Hybrid retrieval (vector + BM25)
    2. Rerank with cross-encoder
    3. Return top-N results
    """
    start_time = time.time()

    try:
        # 1. Hybrid retrieval
        retrieved_docs = retriever.retrieve(
            query=request.query,
            k_vector=request.k,
            k_bm25=request.k + 4,  # Fetch more for BM25
            top_k=request.k
        )

        # 2. Rerank
        if request.rerank_top_n > 0 and len(retrieved_docs) > request.rerank_top_n:
            retrieved_docs = reranker.rerank(
                query=request.query,
                documents=retrieved_docs,
                top_n=request.rerank_top_n
            )

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Retrieved {len(retrieved_docs)} documents for query '{request.query[:50]}...' "
            f"in {elapsed_ms}ms"
        )

        return RetrievalResponse(
            hits=retrieved_docs,
            latency_ms=elapsed_ms
        )

    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
