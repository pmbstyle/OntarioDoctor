"""API Gateway - Public-facing API"""

import time
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.shared.models import (
    ChatRequest,
    ChatResponse,
    IngestRequest,
    IngestResponse,
    HealthResponse,
    ServiceHealth
)
from backend.shared.utils import setup_logging
from backend.gateway.config import settings


# Setup logging
logger = setup_logging("gateway", level=getattr(__import__('logging'), settings.log_level))

# Initialize FastAPI app
app = FastAPI(
    title="OntarioDoctor API Gateway",
    version="1.0.0",
    description="Canadian medical symptom-checker for Ontario residents"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("Starting API Gateway...")
    logger.info(f"Orchestrator URL: {settings.orchestrator_url}")
    logger.info(f"RAG URL: {settings.rag_url}")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info("API Gateway started successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OntarioDoctor API Gateway",
        "version": "1.0.0",
        "region": "Ontario, Canada",
        "endpoints": {
            "chat": "POST /chat",
            "ingest": "POST /ingest",
            "health": "GET /health"
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - symptom checking with RAG

    Args:
        request: Chat request with messages

    Returns:
        Chat response with answer, citations, triage level
    """
    start_time = time.time()

    try:
        logger.info(f"Chat request with {len(request.messages)} messages")

        # Forward to orchestrator
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.orchestrator_url}/run",
                json=request.model_dump()
            )
            response.raise_for_status()

            result = response.json()

        # Add latency
        elapsed_ms = int((time.time() - start_time) * 1000)
        result["latency_ms"] = elapsed_ms

        logger.info(f"Chat completed in {elapsed_ms}ms")

        return ChatResponse(**result)

    except httpx.HTTPStatusError as e:
        logger.error(f"Orchestrator error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Orchestrator error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Ingest endpoint - upload documents for RAG

    Args:
        request: Ingest request with documents

    Returns:
        Ingest response with counts
    """
    try:
        logger.info(f"Ingesting {len(request.documents)} documents")

        # Forward to RAG service
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.rag_url}/ingest",
                json=request.model_dump()
            )
            response.raise_for_status()

            result = response.json()

        logger.info(f"Ingestion completed: {result}")

        return IngestResponse(**result)

    except httpx.HTTPStatusError as e:
        logger.error(f"RAG error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"RAG error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Ingest failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint - check all services

    Returns:
        Health status of all services
    """
    services = []

    # Check orchestrator
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.orchestrator_url}/health")
            response.raise_for_status()
            latency = int((time.time() - start) * 1000)
            services.append(ServiceHealth(
                name="orchestrator",
                status="healthy",
                latency_ms=latency
            ))
    except Exception as e:
        services.append(ServiceHealth(
            name="orchestrator",
            status="unhealthy",
            error=str(e)
        ))

    # Check RAG
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.rag_url}/health")
            response.raise_for_status()
            latency = int((time.time() - start) * 1000)
            services.append(ServiceHealth(
                name="rag",
                status="healthy",
                latency_ms=latency
            ))
    except Exception as e:
        services.append(ServiceHealth(
            name="rag",
            status="unhealthy",
            error=str(e)
        ))

    # Determine overall status
    if all(s.status == "healthy" for s in services):
        overall_status = "healthy"
    elif any(s.status == "healthy" for s in services):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        services=services
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
