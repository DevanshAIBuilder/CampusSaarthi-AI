"""
Citation service.

Assigns stable source IDs to retrieved chunks and validates
that the answer references only actually retrieved sources.
"""
from __future__ import annotations

import re
from typing import List, Dict, Tuple

from app.schemas.chat import SourceCitation


def build_citations(retrieved_chunks: List[dict]) -> Tuple[List[SourceCitation], Dict[str, dict]]:
    """
    Create SourceCitation objects and an ID-to-chunk lookup.

    Returns (citations_list, source_map).
    source_map keys are used as [1], [2], … inline references.
    """
    citations: List[SourceCitation] = []
    source_map: Dict[str, dict] = {}

    for i, chunk in enumerate(retrieved_chunks):
        source_id = str(i + 1)
        excerpt = chunk["text"][:300].strip()
        if len(chunk["text"]) > 300:
            excerpt += "…"

        citation = SourceCitation(
            source_id=source_id,
            document_id=chunk["document_id"],
            filename=chunk["filename"],
            page=chunk.get("page_number"),
            excerpt=excerpt,
            relevance_score=chunk.get("relevance_score", 0.0),
        )
        citations.append(citation)
        source_map[source_id] = chunk

    return citations, source_map


def validate_citations_in_answer(answer: str, source_map: Dict[str, dict]) -> str:
    """
    Remove inline citation markers in the answer that reference non-existent sources.
    Keeps only [N] references where N exists in source_map.
    """
    valid_ids = set(source_map.keys())

    def replace_invalid(match: re.Match) -> str:
        ref = match.group(1)
        if ref in valid_ids:
            return f"[{ref}]"
        return ""  # Remove hallucinated citation

    cleaned = re.sub(r"\[(\d+)\]", replace_invalid, answer)
    return cleaned.strip()


def detect_conflicts(retrieved_chunks: List[dict]) -> Tuple[bool, str | None]:
    """
    Heuristic conflict detection: look for numerical values (dates, fees, amounts)
    that differ across documents.

    Returns (conflict_found, conflict_note).
    """
    import re
    from collections import defaultdict

    # Find monetary amounts and years
    amount_pattern = re.compile(r"(?:Rs\.?\s*|INR\s*|₹\s*)(\d[\d,]+)")
    year_pattern = re.compile(r"\b(20\d{2})\b")

    doc_amounts: dict = defaultdict(set)
    doc_years: dict = defaultdict(set)

    for chunk in retrieved_chunks:
        doc_id = chunk["document_id"]
        amounts = set(m.replace(",", "") for m in amount_pattern.findall(chunk["text"]))
        years = set(year_pattern.findall(chunk["text"]))
        doc_amounts[doc_id].update(amounts)
        doc_years[doc_id].update(years)

    # Cross-document conflict: same key, different values
    all_amounts = set()
    conflicts = []
    for doc_id, amounts in doc_amounts.items():
        overlap = all_amounts & amounts
        if overlap and any(v not in amounts for v in all_amounts):
            conflicts.append(f"Different fee/amount values appear across documents.")
        all_amounts.update(amounts)

    if conflicts:
        return True, (" ".join(conflicts) +
                      " Please review the Sources section and verify with official university records.")

    return False, None
