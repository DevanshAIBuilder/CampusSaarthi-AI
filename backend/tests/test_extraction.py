"""Tests for text extraction service."""
import os
import tempfile
import pytest
from app.services.extraction import extract_txt, extract_document, _normalize_text


def test_normalize_text_collapses_blank_lines():
    raw = "Line 1\n\n\n\nLine 2"
    result = _normalize_text(raw)
    assert "\n\n\n" not in result
    assert "Line 1" in result
    assert "Line 2" in result


def test_extract_txt_basic():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Hello University\nThis is a test document with fee structure.\n")
        fname = f.name
    try:
        result = extract_txt(fname)
        assert result.error is None
        assert result.total_pages == 1
        assert len(result.pages) == 1
        assert not result.pages[0].is_empty
        assert "fee structure" in result.pages[0].text
    finally:
        os.unlink(fname)


def test_extract_txt_empty():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("   \n  \n  ")
        fname = f.name
    try:
        result = extract_txt(fname)
        assert result.pages[0].is_empty
    finally:
        os.unlink(fname)


def test_extract_unsupported_extension():
    result = extract_document("/fake/path/file.docx")
    assert result.error is not None
    assert "Unsupported" in result.error


def test_extract_txt_preserves_numbers():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Fee: Rs. 15,000 per semester\nDeadline: 15 November 2026\n")
        fname = f.name
    try:
        result = extract_txt(fname)
        assert "15,000" in result.pages[0].text
        assert "15 November 2026" in result.pages[0].text
    finally:
        os.unlink(fname)
