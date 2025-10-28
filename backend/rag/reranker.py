"""Cross-encoder reranking service"""

import logging
from typing import List
import torch
from sentence_transformers import CrossEncoder

from backend.shared.models import RetrievedDocument
from backend.shared.constants import RERANKER_MODEL


logger = logging.getLogger(__name__)


class RerankerService:
    """Cross-encoder reranking service"""

    def __init__(self):
        logger.info(f"Loading reranker model: {RERANKER_MODEL}")

        # Detect device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Load model
        self.model = CrossEncoder(RERANKER_MODEL, device=self.device)
        logger.info(f"Reranker model loaded successfully")

    def rerank(
        self,
        query: str,
        documents: List[RetrievedDocument],
        top_n: int = 3
    ) -> List[RetrievedDocument]:
        """
        Rerank documents using cross-encoder

        Args:
            query: Search query
            documents: List of documents to rerank
            top_n: Number of top documents to return

        Returns:
            Top-N reranked documents
        """
        if not documents:
            return []

        if len(documents) <= top_n:
            return documents

        # Prepare query-document pairs
        pairs = [[query, doc.text] for doc in documents]

        # Get cross-encoder scores
        scores = self.model.predict(pairs, show_progress_bar=False)

        # Sort by score
        scored_docs = [
            (score, doc) for score, doc in zip(scores, documents)
        ]
        scored_docs.sort(reverse=True, key=lambda x: x[0])

        # Update scores and return top-N
        reranked = []
        for score, doc in scored_docs[:top_n]:
            doc.score = float(score)  # Update with reranker score
            reranked.append(doc)

        logger.info(f"Reranked {len(documents)} documents → top {len(reranked)}")
        return reranked
