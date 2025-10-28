"""Orchestrator service configuration"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Orchestrator service settings"""

    # Service
    host: str = "0.0.0.0"
    port: int = 8002

    # Dependencies
    rag_url: str = "http://localhost:8001"
    vllm_url: str = "http://localhost:8000"  # vLLM service (port 8000 internal)

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "ORCHESTRATOR_"


settings = Settings()
