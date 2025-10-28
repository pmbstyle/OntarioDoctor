"""Retrieve node - Call RAG service"""

import logging
import httpx
from typing import Dict, Any

from backend.shared.models import RetrievalRequest


logger = logging.getLogger(__name__)


async def retrieve_documents(state: Dict[str, Any], rag_url: str = "http://localhost:8001") -> Dict[str, Any]:
    """
    Retrieve relevant documents from RAG service

    Args:
        state: LangGraph state with features
        rag_url: RAG service URL

    Returns:
        Updated state with retrieved_docs
    """
    features = state.get("features")
    if not features or not hasattr(features, "query_terms"):
        logger.warning("No query terms available for retrieval")
        state["retrieved_docs"] = []
        return state

    # Build query from features
    query_parts = features.query_terms if features.query_terms else []

    # Add age context
    if features.age is not None:
        if features.age == 0:
            query_parts.append("infant")
        elif features.age < 12:
            query_parts.append("child")

    # Add meds if present
    if features.meds:
        query_parts.extend(features.meds)

    query = " ".join(query_parts)
    logger.info(f"Retrieving documents for query: '{query}'")

    # Call RAG service
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            request = RetrievalRequest(
                query=query,
                k=8,
                rerank_top_n=3
            )
            response = await client.post(
                f"{rag_url}/retrieve",
                json=request.model_dump()
            )
            response.raise_for_status()

            result = response.json()
            retrieved_docs = result.get("hits", [])

            logger.info(f"Retrieved {len(retrieved_docs)} documents")
            state["retrieved_docs"] = retrieved_docs

    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        state["retrieved_docs"] = []

    return state
