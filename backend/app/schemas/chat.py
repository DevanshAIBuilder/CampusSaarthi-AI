"""Pydantic request/response schemas for the chat API."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class MessageContext(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., max_length=8192)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID for follow-ups")
    conversation_history: Optional[List[MessageContext]] = Field(
        default=None, max_length=20, description="Recent conversation turns"
    )


class SourceCitation(BaseModel):
    source_id: str
    document_id: str
    filename: str
    page: Optional[int] = None
    excerpt: str
    relevance_score: float


class ChatResponse(BaseModel):
    request_id: str
    conversation_id: str
    answer: str
    abstained: bool = False
    abstention_reason: Optional[str] = None
    citations: List[SourceCitation] = []
    conflict_detected: bool = False
    conflict_note: Optional[str] = None
    retrieval_count: int = 0
    processing_time_ms: float
