"""Application configuration via environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"

    # Admin auth (simple HTTP Basic for hackathon)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "campussaarthi2026"

    # Model configuration
    MODEL_PROVIDER: str = "huggingface"          # huggingface | hf_api | gemini
    MODEL_ID: str = "google/gemma-2-2b-it"       # swap for larger model on capable hardware
    MODEL_PATH: Optional[str] = None             # local override path
    HF_API_TOKEN: Optional[str] = None           # for gated models or HF Inference API
    GEMINI_API_KEY: Optional[str] = None

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Generation
    MAX_NEW_TOKENS: int = 512
    TEMPERATURE: float = 0.1
    MAX_CONTEXT_LENGTH: int = 4096

    # Retrieval
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_THRESHOLD: float = 0.35   # minimum relevance score (0-1)

    # Storage
    DATA_DIR: str = "data"
    VECTOR_INDEX_PATH: str = "data/indexes/faiss.index"
    DATABASE_URL: str = "sqlite+aiosqlite:///data/campussaarthi.db"
    MAX_UPLOAD_SIZE_MB: int = 20

    @property
    def allowed_origins(self) -> List[str]:
        origins = [self.FRONTEND_URL]
        if self.APP_ENV == "development":
            origins += ["http://localhost:3000", "http://127.0.0.1:3000"]
        return origins

    @property
    def upload_dir(self) -> str:
        return os.path.join(self.DATA_DIR, "uploads")

    @property
    def index_dir(self) -> str:
        return os.path.join(self.DATA_DIR, "indexes")

    @property
    def demo_dir(self) -> str:
        return os.path.join(self.DATA_DIR, "demo")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
