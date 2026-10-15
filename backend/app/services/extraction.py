"""
PDF and text extraction service.

Uses PyMuPDF (fitz) for PDF extraction.
Returns page-level text with metadata.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    page_number: int          # 1-indexed
    text: str
    char_count: int
    is_empty: bool
    extraction_note: Optional[str] = None


@dataclass
class ExtractionResult:
    filename: str
    total_pages: int
    pages: List[PageContent] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def non_empty_pages(self) -> List[PageContent]:
        return [p for p in self.pages if not p.is_empty]


def _normalize_text(text: str) -> str:
    """Normalize whitespace while preserving structure."""
    # Collapse multiple blank lines to at most 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Normalize spaces within lines
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def extract_pdf(file_path: str | Path) -> ExtractionResult:
    """Extract text from a PDF file page by page."""
    path = Path(file_path)
    result = ExtractionResult(filename=path.name, total_pages=0)

    try:
        import fitz  # PyMuPDF
    except ImportError:
        result.error = "PyMuPDF is not installed. Run: pip install PyMuPDF"
        return result

    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        result.error = f"Failed to open PDF: {exc}"
        return result

    result.total_pages = doc.page_count

    for page_idx in range(doc.page_count):
        page_num = page_idx + 1
        try:
            page = doc[page_idx]
            raw_text = page.get_text("text")
            normalized = _normalize_text(raw_text)
            is_empty = len(normalized.strip()) < 10

            note = None
            if is_empty and page.get_images():
                note = "Page appears to contain images only. OCR may be required."
                result.warnings.append(f"Page {page_num}: {note}")

            result.pages.append(PageContent(
                page_number=page_num,
                text=normalized,
                char_count=len(normalized),
                is_empty=is_empty,
                extraction_note=note,
            ))
        except Exception as exc:
            logger.warning("Failed to extract page %d: %s", page_num, exc)
            result.pages.append(PageContent(
                page_number=page_num,
                text="",
                char_count=0,
                is_empty=True,
                extraction_note=f"Extraction error: {exc}",
            ))
            result.warnings.append(f"Page {page_num}: extraction error – {exc}")

    doc.close()
    logger.info("Extracted %d/%d non-empty pages from '%s'", len(result.non_empty_pages), result.total_pages, path.name)
    return result


def extract_txt(file_path: str | Path) -> ExtractionResult:
    """Extract text from a plain-text file."""
    path = Path(file_path)
    result = ExtractionResult(filename=path.name, total_pages=1)
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        normalized = _normalize_text(raw)
        result.pages.append(PageContent(
            page_number=1,
            text=normalized,
            char_count=len(normalized),
            is_empty=len(normalized.strip()) < 10,
        ))
    except Exception as exc:
        result.error = f"Failed to read text file: {exc}"
    return result


def extract_document(file_path: str | Path) -> ExtractionResult:
    """Dispatch extraction by file extension."""
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    elif ext == ".txt":
        return extract_txt(path)
    else:
        result = ExtractionResult(filename=path.name, total_pages=0)
        result.error = f"Unsupported file type: {ext}. Supported: .pdf, .txt"
        return result
