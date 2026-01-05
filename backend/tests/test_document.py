"""Tests for document processor."""
import pytest
from io import BytesIO

from translator.document_processor import DocumentProcessor


def test_supported_formats():
    """Test file format validation."""
    assert DocumentProcessor.is_supported("test.pdf")
    assert DocumentProcessor.is_supported("test.docx")
    assert DocumentProcessor.is_supported("test.txt")
    assert not DocumentProcessor.is_supported("test.xyz")
    assert not DocumentProcessor.is_supported("test.jpg")


def test_text_chunking_small():
    """Test chunking of small text."""
    text = "This is a small text."
    chunks = DocumentProcessor.chunk_text(text, chunk_size=1000)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_text_chunking_large():
    """Test chunking of large text."""
    # Create text larger than chunk size
    paragraph = "This is a test paragraph. " * 50
    text = "\n\n".join([paragraph] * 5)
    
    chunks = DocumentProcessor.chunk_text(text, chunk_size=500)
    assert len(chunks) > 1
    
    # Verify all chunks are within size limit (with some margin for split logic)
    for chunk in chunks:
        assert len(chunk) <= 600  # Allow some margin


def test_extract_text_from_txt():
    """Test TXT file text extraction."""
    content = "Hello, this is a test file.\nSecond line."
    file = BytesIO(content.encode('utf-8'))
    
    text = DocumentProcessor.extract_text_from_txt(file)
    assert text == content


def test_extract_text_from_txt_invalid():
    """Test TXT extraction handles errors."""
    # Empty file
    file = BytesIO(b"")
    text = DocumentProcessor.extract_text_from_txt(file)
    assert text == ""


def test_save_translated_document_txt():
    """Test saving translated document as TXT."""
    text = "Translated text content"
    result = DocumentProcessor.save_translated_document(
        "original.txt",
        text,
        "txt"
    )
    assert result == text.encode('utf-8')


def test_save_translated_document_unsupported():
    """Test saving with unsupported format raises error."""
    with pytest.raises(ValueError, match="Unsupported output format"):
        DocumentProcessor.save_translated_document(
            "test.txt",
            "content",
            "xyz"
        )
