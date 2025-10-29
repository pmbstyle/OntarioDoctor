import logging
from typing import List
import torch
from sentence_transformers import SentenceTransformer

from backend.shared.constants import EMBEDDING_MODEL


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Text embedding service"""

    def __init__(self):
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")

        # Detect device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Load model
        self.model = SentenceTransformer(EMBEDDING_MODEL, device=self.device)
        logger.info(f"Embedding model loaded successfully")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (normalized)
        """
        # Encode texts
        embeddings = self.model.encode(
            texts,
            convert_to_tensor=True,
            normalize_embeddings=True,  # L2 normalization
            show_progress_bar=False
        )

        # Convert to list of lists
        return embeddings.cpu().tolist()

    def embed_single(self, text: str) -> List[float]:
        """
        Embed a single text

        Args:
            text: Text string to embed

        Returns:
            Embedding vector (normalized)
        """
        return self.embed([text])[0]
