"""Health check endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.services import vector_store
from app.services.model_adapter import get_adapter

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health():
    adapter = get_adapter()
    stats = vector_store.index_stats()
    return {
        "status": "ok",
        "app": "CampusSaarthi AI",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "model_available": adapter.is_available,
        "model_id": adapter.model_id,
        "embedding_model": settings.EMBEDDING_MODEL,
        "indexed_vectors": stats["total_vectors"],
    }


@router.get("/api/v1/config")
async def public_config():
    """Return safe public config — no secrets."""
    adapter = get_adapter()
    stats = vector_store.index_stats()
    return {
        "model_provider": settings.MODEL_PROVIDER,
        "model_id": adapter.model_id,
        "model_available": adapter.is_available,
        "embedding_model": settings.EMBEDDING_MODEL,
        "retrieval_top_k": settings.RETRIEVAL_TOP_K,
        "retrieval_threshold": settings.RETRIEVAL_THRESHOLD,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "indexed_vectors": stats["total_vectors"],
        "features": {
            "citations": True,
            "abstention": True,
            "conflict_detection": True,
            "conversation_memory": True,
        },
    }
