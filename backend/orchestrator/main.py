from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.shared.models import ChatRequest, ChatResponse
from backend.shared.utils import setup_logging
from backend.orchestrator.config import settings
from backend.orchestrator.graph import run_graph


# Setup logging
logger = setup_logging("orchestrator", level=getattr(__import__('logging'), settings.log_level))

# Initialize FastAPI app
app = FastAPI(title="Orchestrator Service", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.lifespan("startup")
async def startup_event():
    """Startup event"""
    logger.info("Starting orchestrator service...")
    logger.info(f"RAG URL: {settings.rag_url}")
    logger.info(f"Ollama URL: {settings.ollama_url}")
    logger.info("Orchestrator service started successfully")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "rag_url": settings.rag_url,
        "ollama_url": settings.ollama_url
    }


@app.post("/run", response_model=ChatResponse)
async def run_orchestrator(request: ChatRequest):
    """
    Run orchestrator workflow

    Workflow:
    1. Extract features from messages
    2. Check red flags
    3. Retrieve documents (if not ER)
    4. Assemble context with citations
    5. Generate answer with Ollama
    6. Log trace

    Args:
        request: Chat request with messages

    Returns:
        Chat response with answer and citations
    """
    try:
        logger.info(f"Running orchestrator for {len(request.messages)} messages")

        # Run graph
        final_state = await run_graph(
            messages=request.messages,
            rag_url=settings.rag_url,
            ollama_url=settings.ollama_url
        )

        # Build response
        response = ChatResponse(
            answer=final_state.get("answer", ""),
            citations=final_state.get("citations", []),
            triage=final_state.get("triage", "primary-care"),
            red_flags=final_state.get("red_flag_check", {}).red_flags if final_state.get("red_flag_check") else []
        )

        logger.info(f"Orchestrator completed: triage={response.triage}, citations={len(response.citations)}")
        return response

    except Exception as e:
        logger.error(f"Orchestrator failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
