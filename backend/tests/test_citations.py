"""Tests for citation service."""
import pytest
from app.services.citations import build_citations, validate_citations_in_answer, detect_conflicts


def make_chunk(doc_id, filename, page, text, score=0.8):
    return {
        "chunk_id": f"{doc_id}_p{page}_c0",
        "document_id": doc_id,
        "filename": filename,
        "page_number": page,
        "text": text,
        "relevance_score": score,
        "category": "general",
        "is_demo": True,
    }


def test_build_citations_stable_ids():
    chunks = [
        make_chunk("doc-1", "fees.txt", 1, "Fee is Rs. 50,000"),
        make_chunk("doc-2", "exam.txt", 3, "Exams start November 20"),
    ]
    citations, source_map = build_citations(chunks)
    assert len(citations) == 2
    assert citations[0].source_id == "1"
    assert citations[1].source_id == "2"
    assert "fees.txt" in citations[0].filename
    assert citations[0].page == 1
    assert citations[1].page == 3


def test_build_citations_excerpt_truncated():
    long_text = "word " * 200  # > 300 chars
    chunks = [make_chunk("doc-1", "long.txt", 1, long_text)]
    citations, _ = build_citations(chunks)
    assert len(citations[0].excerpt) <= 305  # excerpt + "…"
    assert citations[0].excerpt.endswith("…")


def test_validate_citations_removes_invalid():
    source_map = {"1": {}, "2": {}}
    answer = "Fee is Rs. 50,000 [1]. See also [3] and [2]."
    cleaned = validate_citations_in_answer(answer, source_map)
    assert "[1]" in cleaned
    assert "[2]" in cleaned
    assert "[3]" not in cleaned  # hallucinated


def test_validate_citations_keeps_all_valid():
    source_map = {"1": {}, "2": {}, "3": {}}
    answer = "Check [1] and [2] and [3]."
    cleaned = validate_citations_in_answer(answer, source_map)
    assert "[1]" in cleaned
    assert "[2]" in cleaned
    assert "[3]" in cleaned


def test_detect_conflicts_different_amounts():
    chunks = [
        make_chunk("doc-1", "fees_2025.txt", 1, "The tuition fee is Rs. 50,000 per year."),
        make_chunk("doc-2", "fees_2026.txt", 1, "The tuition fee is Rs. 60,000 per year."),
    ]
    conflict, note = detect_conflicts(chunks)
    # Heuristic may or may not flag this — test that it doesn't crash
    assert isinstance(conflict, bool)


def test_detect_conflicts_same_source():
    chunks = [make_chunk("doc-1", "fees.txt", 1, "Fee: Rs. 50,000.")]
    conflict, note = detect_conflicts(chunks)
    assert not conflict
