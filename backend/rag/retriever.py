"""Hybrid retrieval service (Vector + BM25)"""

import logging
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

from backend.shared.models import RetrievedDocument
from backend.shared.constants import (
    DEFAULT_K_VECTOR,
    DEFAULT_K_BM25,
    TENANT,
    LANGUAGE
)
from backend.rag.qdrant_client import QdrantService
from backend.rag.embedder import EmbeddingService


logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid retrieval combining vector search and BM25"""

    def __init__(self, qdrant_service: QdrantService, embedding_service: EmbeddingService):
        self.qdrant = qdrant_service
        self.embedder = embedding_service

        # BM25 index (in-memory)
        self.bm25_index = None
        self.bm25_docs = []  # Store documents for BM25

    def index_for_bm25(self, documents: List[Dict[str, Any]]):
        """
        Build BM25 index from documents

        Args:
            documents: List of document dicts with 'text' field
        """
        self.bm25_docs = documents
        tokenized_corpus = [doc["text"].lower().split() for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_corpus)
        logger.info(f"BM25 index built with {len(documents)} documents")

    def retrieve(
        self,
        query: str,
        k_vector: int = DEFAULT_K_VECTOR,
        k_bm25: int = DEFAULT_K_BM25,
        top_k: int = None
    ) -> List[RetrievedDocument]:
        """
        Hybrid retrieval: Vector + BM25 with RRF fusion

        Args:
            query: Search query
            k_vector: Number of vector search results
            k_bm25: Number of BM25 results
            top_k: Final number of results after fusion (default: k_vector)

        Returns:
            List of retrieved documents sorted by fused score
        """
        if top_k is None:
            top_k = k_vector

        # 1. Vector search
        query_embedding = self.embedder.embed_single(query)
        vector_hits = self.qdrant.search(
            query_vector=query_embedding,
            limit=k_vector,
            filters={"tenant": TENANT, "lang": LANGUAGE}
        )

        # 2. BM25 search
        bm25_hits = []
        if self.bm25_index and self.bm25_docs:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25_index.get_scores(tokenized_query)

            # Get top-k BM25 results
            top_indices = sorted(
                range(len(bm25_scores)),
                key=lambda i: bm25_scores[i],
                reverse=True
            )[:k_bm25]

            for idx in top_indices:
                doc = self.bm25_docs[idx]
                # Filter by tenant
                if doc.get("tenant") == TENANT:
                    bm25_hits.append({
                        **doc,
                        "score": float(bm25_scores[idx])
                    })

        # 3. Reciprocal Rank Fusion (RRF)
        fused_scores = {}
        k_rrf = 60  # RRF constant

        # Add vector search ranks
        for rank, hit in enumerate(vector_hits, start=1):
            doc_id = hit["doc_id"]
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k_rrf + rank)

        # Add BM25 ranks
        for rank, hit in enumerate(bm25_hits, start=1):
            doc_id = hit["doc_id"]
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k_rrf + rank)

        # 4. Combine and deduplicate
        all_docs = {}
        for hit in vector_hits + bm25_hits:
            doc_id = hit["doc_id"]
            if doc_id not in all_docs:
                all_docs[doc_id] = hit

        # 5. Sort by fused score
        sorted_docs = sorted(
            all_docs.items(),
            key=lambda x: fused_scores.get(x[0], 0),
            reverse=True
        )[:top_k]

        # 6. Convert to RetrievedDocument
        results = []
        for doc_id, doc in sorted_docs:
            results.append(RetrievedDocument(
                doc_id=doc["doc_id"],
                text=doc["text"],
                url=doc["url"],
                source=doc["source"],
                title=doc["title"],
                chunk_id=doc["chunk_id"],
                score=fused_scores[doc_id]
            ))

        logger.info(
            f"Hybrid retrieval: {len(vector_hits)} vector + {len(bm25_hits)} BM25 "
            f"→ {len(results)} fused results"
        )
        return results
