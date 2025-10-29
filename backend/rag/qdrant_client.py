import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from qdrant_client.http.exceptions import UnexpectedResponse

from backend.shared.constants import (
    QDRANT_COLLECTION_NAME,
    QDRANT_DISTANCE,
    EMBEDDING_DIM
)


logger = logging.getLogger(__name__)


class QdrantService:
    """Qdrant vector database service"""

    def __init__(self, url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.collection_name = QDRANT_COLLECTION_NAME
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except (UnexpectedResponse, Exception):
            logger.info(f"Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE if QDRANT_DISTANCE == "Cosine" else Distance.DOT
                )
            )
            logger.info(f"Collection '{self.collection_name}' created successfully")

    def upsert(self, points: List[PointStruct]):
        """Upsert points to collection"""
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} points to Qdrant")

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        # Build filter
        filter_obj = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    # For list values, match any
                    for v in value:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=v))
                        )
                else:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )

            if conditions:
                filter_obj = Filter(must=conditions)

        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_obj
        )

        # Format results
        hits = []
        for result in results:
            hit = {
                "doc_id": result.payload.get("doc_id"),
                "text": result.payload.get("text"),
                "url": result.payload.get("url"),
                "source": result.payload.get("source"),
                "title": result.payload.get("title"),
                "chunk_id": result.payload.get("chunk_id"),
                "score": result.score
            }
            hits.append(hit)

        return hits

    def count(self) -> int:
        """Get total number of points in collection"""
        collection_info = self.client.get_collection(self.collection_name)
        return collection_info.points_count
