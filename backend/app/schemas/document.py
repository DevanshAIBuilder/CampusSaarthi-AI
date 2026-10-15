"""Pydantic schemas for document management."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size_bytes: int
    file_type: str
    category: Optional[str]
    status: str
    total_pages: int
    total_chunks: int
    error_message: Optional[str]
    is_demo: bool
    uploaded_at: datetime
    indexed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentOut]
    total: int


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


class ReindexResponse(BaseModel):
    document_id: str
    status: str
    message: str
