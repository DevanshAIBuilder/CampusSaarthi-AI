"""
Ingestion service – orchestrates extraction, chunking, embedding, and indexing.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document, DocumentStatus
from app.services.extraction import extract_document
from app.services.chunking import chunk_document
from app.services import vector_store

logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def validate_upload(filename: str, content: bytes) -> str | None:
    """Return error message or None if valid."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f"File type '{ext}' is not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    if len(content) > MAX_BYTES:
        return f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB."
    # Basic magic-byte check for PDF
    if ext == ".pdf" and not content.startswith(b"%PDF"):
        return "File does not appear to be a valid PDF."
    return None


def safe_filename(original: str) -> str:
    """Generate a safe server-side filename that cannot escape the upload directory."""
    ext = Path(original).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


async def ingest_document(
    db: AsyncSession,
    document_id: str,
    file_path: str,
    original_filename: str,
    file_size: int,
    file_type: str,
    category: str | None = None,
    is_demo: bool = False,
) -> Document:
    """Run full ingestion pipeline and update document status in DB."""
    # Mark as processing
    result = await db.get(Document, document_id)
    if result is None:
        raise ValueError(f"Document {document_id} not found in database.")

    result.status = DocumentStatus.PROCESSING
    await db.commit()

    try:
        # 1. Extract
        extraction = extract_document(file_path)
        if extraction.error:
            raise RuntimeError(f"Extraction failed: {extraction.error}")

        non_empty = extraction.non_empty_pages
        if not non_empty:
            raise RuntimeError("No readable text found in the document. "
                               "If this is a scanned PDF, OCR is required.")

        # 2. Chunk
        chunks = chunk_document(
            document_id=document_id,
            filename=original_filename,
            pages=non_empty,
            category=category,
            is_demo=is_demo,
        )

        if not chunks:
            raise RuntimeError("Chunking produced no segments.")

        # 3. Index
        added = vector_store.add_chunks(chunks)

        # 4. Update record
        result.status = DocumentStatus.INDEXED
        result.total_pages = extraction.total_pages
        result.total_chunks = added
        result.embedding_model = settings.EMBEDDING_MODEL
        result.indexed_at = datetime.now(timezone.utc)

        if extraction.warnings:
            warning_str = "; ".join(extraction.warnings[:5])
            logger.warning("Ingestion warnings for %s: %s", document_id, warning_str)

        await db.commit()
        await db.refresh(result)
        logger.info("Successfully ingested document %s (%d chunks)", document_id, added)
        return result

    except Exception as exc:
        logger.exception("Ingestion failed for document %s", document_id)
        result.status = DocumentStatus.FAILED
        result.error_message = str(exc)[:1000]
        await db.commit()
        raise


async def create_document_record(
    db: AsyncSession,
    original_filename: str,
    safe_fname: str,
    file_path: str,
    file_size: int,
    file_type: str,
    category: str | None = None,
    is_demo: bool = False,
) -> Document:
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        filename=safe_fname,
        original_filename=original_filename,
        file_path=file_path,
        file_size_bytes=file_size,
        file_type=file_type,
        category=category,
        status=DocumentStatus.PENDING,
        is_demo=is_demo,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc
