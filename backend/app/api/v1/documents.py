"""Document management API endpoints."""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.models.document import Document, DocumentStatus
from app.schemas.document import (
    DocumentListResponse, DocumentOut, DocumentUploadResponse, ReindexResponse
)
from app.services.ingestion import validate_upload, safe_filename, create_document_record, ingest_document
from app.services import vector_store

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form(default="general"),
    is_demo: bool = Form(default=False),
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    content = await file.read()
    error = validate_upload(file.filename or "upload", content)
    if error:
        raise HTTPException(status_code=400, detail=error)

    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_fname = safe_filename(file.filename or "upload")
    file_path = os.path.join(settings.upload_dir, safe_fname)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    ext = Path(file.filename or "upload").suffix.lower().lstrip(".")
    doc = await create_document_record(
        db=db,
        original_filename=file.filename or "upload",
        safe_fname=safe_fname,
        file_path=file_path,
        file_size=len(content),
        file_type=ext,
        category=category,
        is_demo=is_demo,
    )

    # Run ingestion in background so we don't block the upload response
    background_tasks.add_task(_run_ingestion, doc.id, file_path, doc.original_filename,
                               len(content), ext, category, is_demo)

    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.original_filename,
        status=DocumentStatus.PENDING,
        message="Document uploaded. Indexing has started in the background.",
    )


async def _run_ingestion(doc_id: str, file_path: str, original_filename: str,
                          file_size: int, file_type: str, category: str, is_demo: bool):
    """Background ingestion task."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            await ingest_document(
                db=db, document_id=doc_id, file_path=file_path,
                original_filename=original_filename, file_size=file_size,
                file_type=file_type, category=category, is_demo=is_demo,
            )
        except Exception as exc:
            logger.error("Background ingestion failed for %s: %s", doc_id, exc)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.status != DocumentStatus.DELETED).order_by(Document.uploaded_at.desc())
    )
    docs = result.scalars().all()
    return DocumentListResponse(
        documents=[DocumentOut.model_validate(d) for d in docs],
        total=len(docs),
    )


@router.get("/documents/{document_id}", response_model=DocumentOut)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, document_id)
    if not doc or doc.status == DocumentStatus.DELETED:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentOut.model_validate(doc)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    doc = await db.get(Document, document_id)
    if not doc or doc.status == DocumentStatus.DELETED:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove from vector store
    removed_chunks = vector_store.delete_document_chunks(document_id)

    # Remove file
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as exc:
        logger.warning("Could not remove file %s: %s", doc.file_path, exc)

    # Mark as deleted
    doc.status = DocumentStatus.DELETED
    await db.commit()

    return {
        "document_id": document_id,
        "status": "deleted",
        "chunks_removed": removed_chunks,
        "message": f"Document deleted. {removed_chunks} chunks removed from index.",
    }


@router.post("/documents/{document_id}/reindex", response_model=ReindexResponse)
async def reindex_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    doc = await db.get(Document, document_id)
    if not doc or doc.status == DocumentStatus.DELETED:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=409, detail="Original file no longer available for re-indexing.")

    # Remove old chunks
    vector_store.delete_document_chunks(document_id)

    background_tasks.add_task(
        _run_ingestion, doc.id, doc.file_path, doc.original_filename,
        doc.file_size_bytes, doc.file_type, doc.category or "general", doc.is_demo,
    )

    return ReindexResponse(
        document_id=document_id,
        status="pending",
        message="Re-indexing started in the background.",
    )
