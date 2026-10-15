"""Admin statistics endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.document import Document, DocumentStatus
from app.services import vector_store

router = APIRouter()


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    # Document counts by status
    result = await db.execute(
        select(Document.status, func.count(Document.id)).group_by(Document.status)
    )
    status_counts = {row[0]: row[1] for row in result.all()}

    # Total chunks / pages
    result2 = await db.execute(
        select(func.sum(Document.total_chunks), func.sum(Document.total_pages))
        .where(Document.status == DocumentStatus.INDEXED)
    )
    row = result2.first()
    total_chunks = row[0] or 0
    total_pages = row[1] or 0

    idx = vector_store.index_stats()

    return {
        "documents": {
            "total": sum(v for k, v in status_counts.items() if k != DocumentStatus.DELETED),
            "indexed": status_counts.get(DocumentStatus.INDEXED, 0),
            "processing": status_counts.get(DocumentStatus.PROCESSING, 0),
            "failed": status_counts.get(DocumentStatus.FAILED, 0),
            "pending": status_counts.get(DocumentStatus.PENDING, 0),
        },
        "content": {
            "total_indexed_pages": total_pages,
            "total_indexed_chunks": total_chunks,
        },
        "vector_store": idx,
    }
