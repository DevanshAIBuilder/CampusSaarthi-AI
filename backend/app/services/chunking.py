"""
Text chunking service.

Splits extracted page text into configurable overlapping chunks
while preserving source metadata (document_id, filename, page).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 400        # characters
DEFAULT_CHUNK_OVERLAP = 80     # characters


@dataclass
class Chunk:
    chunk_id: str               # {document_id}_p{page}_c{idx}
    document_id: str
    filename: str
    page_number: int
    chunk_index: int            # within-page index
    text: str
    char_count: int
    category: Optional[str] = None
    is_demo: bool = False


def _split_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping character-level chunks at whitespace boundaries."""
    if not text.strip():
        return []

    chunks: List[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to break at whitespace boundary
        if end < text_len:
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Advance with overlap
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks


def chunk_document(
    document_id: str,
    filename: str,
    pages: list,  # List[PageContent]
    category: Optional[str] = None,
    is_demo: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Chunk]:
    """
    Chunk all non-empty pages of a document into retrievable text segments.

    Each chunk carries full source metadata for citation purposes.
    """
    chunks: List[Chunk] = []

    for page in pages:
        if page.is_empty:
            continue

        page_chunks = _split_into_chunks(page.text, chunk_size, chunk_overlap)

        for idx, text in enumerate(page_chunks):
            chunk_id = f"{document_id}_p{page.page_number}_c{idx}"
            chunks.append(Chunk(
                chunk_id=chunk_id,
                document_id=document_id,
                filename=filename,
                page_number=page.page_number,
                chunk_index=idx,
                text=text,
                char_count=len(text),
                category=category,
                is_demo=is_demo,
            ))

    logger.info("Created %d chunks from %d pages for document %s", len(chunks), len(pages), document_id)
    return chunks
