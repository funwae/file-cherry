"""
Tests for document extraction functionality.
"""

import tempfile
from pathlib import Path

import pytest

from src.services.doc_service import DocService, DocumentSegment


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        runtime_dir = Path(tmpdir) / "runtime"
        yield data_dir, runtime_dir


@pytest.fixture
def doc_service(temp_dirs):
    """Create a DocService instance."""
    data_dir, runtime_dir = temp_dirs
    return DocService(data_dir, runtime_dir)


def test_extract_text_file(doc_service, temp_dirs):
    """Test extracting text from plain text file."""
    data_dir, _ = temp_dirs
    test_file = data_dir / "test.txt"
    test_file.write_text("This is a test document.\n\nIt has multiple paragraphs.")

    result = doc_service.extract_text(str(test_file))

    assert result["doc_id"] == str(test_file)
    assert len(result["segments"]) > 0
    assert "test document" in result["segments"][0]["text"]


def test_extract_markdown(doc_service, temp_dirs):
    """Test extracting text from markdown file."""
    data_dir, _ = temp_dirs
    test_file = data_dir / "test.md"
    test_file.write_text("# Title\n\nSome content here.")

    result = doc_service.extract_text(str(test_file))

    assert len(result["segments"]) > 0
    assert "Title" in result["segments"][0]["text"]


def test_extract_nonexistent_file(doc_service):
    """Test extracting from non-existent file."""
    with pytest.raises(FileNotFoundError):
        doc_service.extract_text("nonexistent.txt")


def test_chunk_text_simple(doc_service):
    """Test chunking simple text."""
    text = "A" * 500
    chunks = doc_service.chunk_text(text, chunk_size=200, chunk_overlap=50)

    assert len(chunks) > 0
    assert all(len(chunk) <= 200 for chunk in chunks)


def test_chunk_text_small(doc_service):
    """Test chunking text smaller than chunk size."""
    text = "Short text"
    chunks = doc_service.chunk_text(text, chunk_size=1000)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_overlap(doc_service):
    """Test chunking with overlap."""
    text = "A" * 1000
    chunks = doc_service.chunk_text(text, chunk_size=200, chunk_overlap=50)

    # Should have multiple chunks with overlap
    assert len(chunks) > 1
    # Check that chunks overlap (first chunk end should appear in second chunk start)
    if len(chunks) > 1:
        # Overlap means some content is shared
        assert len(chunks[0]) + len(chunks[1]) > len(text)


def test_document_segment_to_dict():
    """Test DocumentSegment serialization."""
    seg = DocumentSegment(
        segment_id="s1",
        text="Test text",
        page=1,
        heading="Test Heading",
    )

    d = seg.to_dict()
    assert d["segment_id"] == "s1"
    assert d["text"] == "Test text"
    assert d["page"] == 1
    assert d["heading"] == "Test Heading"


def test_extract_csv(doc_service, temp_dirs):
    """Test extracting text from CSV file."""
    data_dir, _ = temp_dirs
    test_file = data_dir / "test.csv"
    test_file.write_text("Name,Age\nJohn,30\nJane,25")

    result = doc_service.extract_text(str(test_file))

    assert len(result["segments"]) > 0
    assert "Name" in result["segments"][0]["text"]


def test_extract_json(doc_service, temp_dirs):
    """Test extracting text from JSON file."""
    data_dir, _ = temp_dirs
    test_file = data_dir / "test.json"
    test_file.write_text('{"key": "value", "number": 42}')

    result = doc_service.extract_text(str(test_file))

    assert len(result["segments"]) > 0
    assert "key" in result["segments"][0]["text"]

