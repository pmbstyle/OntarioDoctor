"""RAG service configuration"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """RAG service settings"""

    # Service
    host: str = "0.0.0.0"
    port: int = 8001

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "RAG_"


settings = Settings()
