"""
Vector store service using FAISS and Sentence Transformers.

Responsibilities:
- Lazy-load the embedding model once.
- Build and persist a FAISS index.
- Store chunk metadata separately (JSON-lines file).
- Support add, search, delete, and full rebuild operations.
"""
from __future__ import annotations

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.core.config import get_settings
from app.services.chunking import Chunk

logger = logging.getLogger(__name__)
settings = get_settings()

# Metadata sidecar paths alongside the FAISS index
_INDEX_PATH = Path(settings.VECTOR_INDEX_PATH)
_METADATA_PATH = _INDEX_PATH.parent / "chunk_metadata.pkl"
_CONFIG_PATH = _INDEX_PATH.parent / "index_config.json"

# Singleton state
_embedding_model = None
_faiss_index = None
_chunk_metadata: Dict[int, dict] = {}   # faiss_row_id -> chunk dict
_embedding_dim: Optional[int] = None


def _get_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        model_name = settings.EMBEDDING_MODEL
        logger.info("Loading embedding model '%s' …", model_name)
        _embedding_model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded.")
    return _embedding_model


def _embed(texts: List[str]) -> np.ndarray:
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)


def _ensure_index_dir():
    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


def _save_state():
    _ensure_index_dir()
    import faiss
    faiss.write_index(_faiss_index, str(_INDEX_PATH))
    with open(_METADATA_PATH, "wb") as f:
        pickle.dump(_chunk_metadata, f)
    config = {
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dim": _embedding_dim,
        "total_chunks": _faiss_index.ntotal,
    }
    with open(_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    logger.debug("FAISS index saved. Total vectors: %d", _faiss_index.ntotal)


def load_index() -> bool:
    """Load persisted index and metadata. Returns True if loaded."""
    global _faiss_index, _chunk_metadata, _embedding_dim

    if not _INDEX_PATH.exists() or not _METADATA_PATH.exists():
        logger.info("No persisted FAISS index found. A fresh index will be created on first upload.")
        return False

    try:
        import faiss
        _faiss_index = faiss.read_index(str(_INDEX_PATH))
        with open(_METADATA_PATH, "rb") as f:
            _chunk_metadata = pickle.load(f)

        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH) as f:
                cfg = json.load(f)
            _embedding_dim = cfg.get("embedding_dim")
            saved_model = cfg.get("embedding_model")
            if saved_model and saved_model != settings.EMBEDDING_MODEL:
                logger.warning(
                    "Index was built with '%s' but current model is '%s'. "
                    "Retrieval quality may be degraded. Consider re-indexing all documents.",
                    saved_model, settings.EMBEDDING_MODEL,
                )

        logger.info("FAISS index loaded. Vectors: %d, Chunks in metadata: %d",
                    _faiss_index.ntotal, len(_chunk_metadata))
        return True
    except Exception as exc:
        logger.error("Failed to load FAISS index: %s", exc)
        _faiss_index = None
        _chunk_metadata = {}
        return False


def _get_or_create_index(dim: int):
    global _faiss_index, _embedding_dim
    if _faiss_index is None or _embedding_dim != dim:
        import faiss
        _faiss_index = faiss.IndexFlatIP(dim)  # inner product on normalised vectors = cosine
        _embedding_dim = dim
        logger.info("Created new FAISS IndexFlatIP(dim=%d)", dim)
    return _faiss_index


def add_chunks(chunks: List[Chunk]) -> int:
    """Embed and add chunks to the index. Returns number of vectors added."""
    global _chunk_metadata

    if not chunks:
        return 0

    texts = [c.text for c in chunks]
    embeddings = _embed(texts)
    dim = embeddings.shape[1]

    index = _get_or_create_index(dim)
    start_id = index.ntotal

    index.add(embeddings)

    for i, chunk in enumerate(chunks):
        _chunk_metadata[start_id + i] = {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "filename": chunk.filename,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "category": chunk.category,
            "is_demo": chunk.is_demo,
        }

    _save_state()
    logger.info("Added %d chunks to FAISS index (total: %d)", len(chunks), index.ntotal)
    return len(chunks)


def search(
    query: str,
    top_k: int = 5,
    threshold: float = 0.35,
) -> List[dict]:
    """
    Search for relevant chunks.

    Returns list of metadata dicts with added 'relevance_score' key.
    Scores are inner-product on L2-normalised vectors ≈ cosine similarity.
    """
    global _faiss_index, _chunk_metadata

    if _faiss_index is None or _faiss_index.ntotal == 0:
        # Try loading from disk
        if not load_index() or _faiss_index is None or _faiss_index.ntotal == 0:
            logger.info("Index empty – no documents indexed yet.")
            return []

    q_emb = _embed([query])
    scores, indices = _faiss_index.search(q_emb, min(top_k * 2, _faiss_index.ntotal))

    results = []
    seen_chunks: set = set()

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        meta = _chunk_metadata.get(int(idx))
        if meta is None:
            continue
        relevance = float(score)
        if relevance < threshold:
            continue
        # Deduplicate by chunk_id (can arise after re-index)
        cid = meta["chunk_id"]
        if cid in seen_chunks:
            continue
        seen_chunks.add(cid)
        results.append({**meta, "relevance_score": round(relevance, 4)})
        if len(results) >= top_k:
            break

    logger.info("Retrieved %d/%d chunks above threshold %.2f for query", len(results), top_k, threshold)
    return results


def delete_document_chunks(document_id: str) -> int:
    """
    Remove all chunks for a document from the metadata store and rebuild the FAISS index.

    FAISS IndexFlatIP does not support selective deletion, so we rebuild from remaining metadata.
    """
    global _faiss_index, _chunk_metadata

    # Identify rows to keep
    keep_rows = {row_id: meta for row_id, meta in _chunk_metadata.items()
                 if meta["document_id"] != document_id}
    removed = len(_chunk_metadata) - len(keep_rows)

    if removed == 0:
        return 0

    logger.info("Removing %d chunks for document %s and rebuilding index…", removed, document_id)

    remaining_chunks = list(keep_rows.values())
    _chunk_metadata = {}
    _faiss_index = None

    if remaining_chunks:
        texts = [m["text"] for m in remaining_chunks]
        embeddings = _embed(texts)
        dim = embeddings.shape[1]
        index = _get_or_create_index(dim)
        index.add(embeddings)
        for i, meta in enumerate(remaining_chunks):
            _chunk_metadata[i] = meta
    else:
        import faiss
        if _embedding_dim:
            _faiss_index = faiss.IndexFlatIP(_embedding_dim)

    _save_state()
    logger.info("Index rebuilt. Remaining vectors: %d", _faiss_index.ntotal if _faiss_index else 0)
    return removed


def index_stats() -> dict:
    global _faiss_index, _chunk_metadata
    if _faiss_index is None:
        load_index()
    return {
        "total_vectors": _faiss_index.ntotal if _faiss_index else 0,
        "total_metadata_entries": len(_chunk_metadata),
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dim": _embedding_dim,
    }
