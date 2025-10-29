from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationError
import sys


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

    @field_validator("orchestrator_url", "rag_url")
    @classmethod
    def validate_url(cls, v: str, info) -> str:
        if not v or not v.startswith(("http://", "https://")):
            raise ValueError(f"{info.field_name} must be a valid HTTP(S) URL")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    class Config:
        env_file = ".env"
        env_prefix = "GATEWAY_"


try:
    settings = Settings()
except ValidationError as e:
    print(f"Configuration validation failed: {e}", file=sys.stderr)
    sys.exit(1)
