"""Assemble node - Build context with citations"""

import logging
from typing import Dict, Any, List

from backend.shared.models import Citation


logger = logging.getLogger(__name__)


def assemble_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assemble context from retrieved documents with citations

    Args:
        state: LangGraph state with retrieved_docs

    Returns:
        Updated state with context_text and citations
    """
    retrieved_docs = state.get("retrieved_docs", [])

    if not retrieved_docs:
        logger.warning("No documents retrieved for context assembly")
        state["context_text"] = "No relevant information found."
        state["citations"] = []
        return state

    # Deduplicate by doc_id (already done in retrieval, but double-check)
    seen_doc_ids = set()
    unique_docs = []
    for doc in retrieved_docs:
        doc_id = doc.get("doc_id", "")
        if doc_id not in seen_doc_ids:
            seen_doc_ids.add(doc_id)
            unique_docs.append(doc)

    # Diversify by source (prefer different sources)
    source_counts = {}
    diversified_docs = []
    max_per_source = 2

    for doc in unique_docs:
        source = doc.get("source", "unknown")
        count = source_counts.get(source, 0)

        if count < max_per_source:
            diversified_docs.append(doc)
            source_counts[source] = count + 1

    # If we don't have enough docs, add more from unique_docs
    if len(diversified_docs) < len(unique_docs):
        for doc in unique_docs:
            if doc not in diversified_docs:
                diversified_docs.append(doc)
                if len(diversified_docs) >= 5:  # Max 5 documents
                    break

    # Build context with numbered citations
    context_lines = []
    citations = []

    for i, doc in enumerate(diversified_docs, start=1):
        # Format: [1] (source#chunk_id) text
        doc_id = doc.get("doc_id", "unknown")
        text = doc.get("text", "")
        source = doc.get("source", "unknown")
        chunk_id = doc.get("chunk_id", 0)

        context_line = f"[{i}] ({source}#{chunk_id}) {text}"
        context_lines.append(context_line)

        # Create citation
        citation = Citation(
            id=i,
            title=doc.get("title", "Unknown"),
            url=doc.get("url", "#"),
            source=source
        )
        citations.append(citation)

    context_text = "\n\n".join(context_lines)

    logger.info(f"Assembled context with {len(citations)} citations")

    state["context_text"] = context_text
    state["citations"] = citations

    return state
