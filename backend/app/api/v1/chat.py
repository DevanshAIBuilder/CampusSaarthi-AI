"""Chat API endpoint."""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import vector_store
from app.services.generation import generate_grounded_answer
from app.services.citations import build_citations, validate_citations_in_answer, detect_conflicts
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    start = time.perf_counter()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    conversation_id = body.conversation_id or str(uuid.uuid4())

    logger.info("Chat request_id=%s, conv=%s, question_len=%d",
                request_id, conversation_id, len(body.question))

    # 1. Retrieve relevant chunks
    try:
        retrieved = vector_store.search(
            query=body.question,
            top_k=settings.RETRIEVAL_TOP_K,
            threshold=settings.RETRIEVAL_THRESHOLD,
        )
    except Exception as exc:
        logger.error("Retrieval error: %s", exc)
        raise HTTPException(status_code=503, detail=f"Retrieval service error: {exc}")

    # 2. Build citations
    citations, source_map = build_citations(retrieved)

    # 3. Conflict detection
    conflict_found, conflict_note = detect_conflicts(retrieved)

    # 4. Convert conversation history to dict list
    history = (
        [m.model_dump() for m in body.conversation_history]
        if body.conversation_history else None
    )

    # 5. Generate grounded answer
    try:
        answer, abstained, abstention_reason = generate_grounded_answer(
            question=body.question,
            retrieved_chunks=retrieved,
            conversation_history=history,
            max_new_tokens=settings.MAX_NEW_TOKENS,
        )
    except Exception as exc:
        logger.error("Generation error: %s", exc)
        raise HTTPException(status_code=503, detail=f"Generation service error: {exc}")

    # 6. Validate citation references
    if not abstained:
        answer = validate_citations_in_answer(answer, source_map)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return ChatResponse(
        request_id=request_id,
        conversation_id=conversation_id,
        answer=answer,
        abstained=abstained,
        abstention_reason=abstention_reason,
        citations=citations,
        conflict_detected=conflict_found,
        conflict_note=conflict_note,
        retrieval_count=len(retrieved),
        processing_time_ms=round(elapsed_ms, 1),
    )
