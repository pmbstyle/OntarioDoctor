from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service
    host: str = "0.0.0.0"
    port: int = 8000

    # Dependencies
    orchestrator_url: str = "http://localhost:8002"
    rag_url: str = "http://localhost:8001"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "GATEWAY_"


settings = Settings()
