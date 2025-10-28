"""Shared constants for all services"""

# ============================================================================
# Regional Settings
# ============================================================================

TENANT = "CA-ON"  # Always Ontario
LANGUAGE = "en"
REGION_NAME = "Ontario"

# ============================================================================
# Model Names
# ============================================================================

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

RERANKER_MODEL = "BAAI/bge-reranker-base"

LLM_MODEL = "google/medgemma-4b-it"

# ============================================================================
# Chunking Parameters
# ============================================================================

CHUNK_SIZE = 700  # tokens
CHUNK_OVERLAP = 120  # tokens

# ============================================================================
# Retrieval Parameters
# ============================================================================

DEFAULT_K_VECTOR = 8  # Vector search results
DEFAULT_K_BM25 = 12  # BM25 search results
DEFAULT_RERANK_TOP_N = 3  # Final reranked results

# ============================================================================
# LLM Parameters
# ============================================================================

LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 512
LLM_TOP_P = 0.95

# ============================================================================
# Qdrant Configuration
# ============================================================================

QDRANT_COLLECTION_NAME = "docs"
QDRANT_DISTANCE = "Cosine"

# ============================================================================
# Ontario-Specific Resources
# ============================================================================

TELEHEALTH_ONTARIO = "1-866-797-0000"
EMERGENCY_NUMBER = "911"

ONTARIO_RESOURCES = {
    "family_doctor": "See your family doctor",
    "walk_in_clinic": "Visit a walk-in clinic",
    "telehealth": f"Call Telehealth Ontario at {TELEHEALTH_ONTARIO}",
    "er": "Go to the Emergency Room",
    "emergency": f"Call {EMERGENCY_NUMBER} immediately"
}
