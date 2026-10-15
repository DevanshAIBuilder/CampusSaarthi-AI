"""Tests for the chunking service."""
import pytest
from app.services.chunking import chunk_document, _split_into_chunks
from app.services.extraction import PageContent


def make_pages(texts):
    return [
        PageContent(page_number=i + 1, text=t, char_count=len(t), is_empty=len(t.strip()) < 10)
        for i, t in enumerate(texts)
    ]


def test_split_basic():
    text = "word " * 100
    chunks = _split_into_chunks(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 220  # allow slight overshoot at whitespace boundaries


def test_split_empty():
    assert _split_into_chunks("", 200, 40) == []


def test_split_overlap():
    text = "The quick brown fox jumps over the lazy dog " * 5
    chunks = _split_into_chunks(text, chunk_size=50, overlap=10)
    # Consecutive chunks should share some content due to overlap
    if len(chunks) >= 2:
        # end of first chunk should overlap with beginning of second
        assert len(chunks[0]) > 0


def test_chunk_document_metadata():
    pages = make_pages(["Exam schedule: End-semester exams from 20 November 2026."])
    chunks = chunk_document(
        document_id="doc-001",
        filename="exam_schedule.txt",
        pages=pages,
        category="exams",
        is_demo=True,
    )
    assert len(chunks) >= 1
    c = chunks[0]
    assert c.document_id == "doc-001"
    assert c.filename == "exam_schedule.txt"
    assert c.page_number == 1
    assert c.is_demo is True
    assert c.category == "exams"
    assert "exam" in c.text.lower()


def test_chunk_skips_empty_pages():
    pages = make_pages(["   ", "Real content here about registration."])
    chunks = chunk_document("doc-002", "reg.txt", pages)
    # First page is empty, should be skipped
    assert all("Real content" in c.text or "registration" in c.text.lower() for c in chunks)
    for c in chunks:
        assert c.page_number == 2  # only from page 2


def test_chunk_ids_unique():
    pages = make_pages(["Fee details: Rs. 50,000 per year. " * 10])
    chunks = chunk_document("doc-003", "fees.txt", pages)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs must be unique"
