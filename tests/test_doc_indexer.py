"""
Tests for document indexing functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest

from src.services.doc_indexer import DocIndexer, DocumentIndex
from src.services.doc_service import DocService


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_dir = Path(tmpdir) / "runtime"
        yield runtime_dir


@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client."""
    client = Mock()
    client._request = Mock(return_value={"embedding": [0.1] * 384})
    return client


def test_document_index_init(temp_dirs):
    """Test DocumentIndex initialization."""
    index = DocumentIndex(temp_dirs)
    assert index.index_dir == temp_dirs
    assert index.embeddings is None
    assert index.metadata == []


def test_document_index_add_segments(temp_dirs):
    """Test adding segments to index."""
    index = DocumentIndex(temp_dirs)

    embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    metadata = [
        {"doc_id": "doc1", "text": "text1"},
        {"doc_id": "doc2", "text": "text2"},
    ]

    index.add_segments(embeddings, metadata)

    assert index.embeddings is not None
    assert len(index.metadata) == 2
    assert index.embeddings.shape[0] == 2


def test_document_index_search(temp_dirs):
    """Test searching the index."""
    index = DocumentIndex(temp_dirs)

    # Add some segments
    embeddings = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    metadata = [
        {"doc_id": "doc1", "text": "apple"},
        {"doc_id": "doc2", "text": "banana"},
        {"doc_id": "doc3", "text": "cherry"},
    ]

    index.add_segments(embeddings, metadata)

    # Search for something similar to first embedding
    query_embedding = np.array([0.9, 0.1, 0.0])
    results = index.search(query_embedding, top_n=2)

    assert len(results) == 2
    assert results[0]["doc_id"] == "doc1"  # Should be most similar


def test_doc_indexer_init(temp_dirs, mock_ollama_client):
    """Test DocIndexer initialization."""
    indexer = DocIndexer(
        temp_dirs,
        chunk_size=512,
        chunk_overlap=64,
        use_ollama=True,
        ollama_client=mock_ollama_client,
    )

    assert indexer.chunk_size == 512
    assert indexer.chunk_overlap == 64
    assert indexer.use_ollama is True


def test_doc_indexer_index_document(temp_dirs, mock_ollama_client):
    """Test indexing a document."""
    indexer = DocIndexer(
        temp_dirs,
        use_ollama=True,
        ollama_client=mock_ollama_client,
    )

    doc_service = DocService(Path("/tmp"), temp_dirs)

    segments = [
        {"segment_id": "s1", "text": "This is a test document with some content."},
        {"segment_id": "s2", "text": "More content here in another segment."},
    ]

    count = indexer.index_document("test_doc", segments, doc_service)

    assert count > 0
    stats = indexer.get_stats()
    assert stats["total_segments"] > 0


def test_doc_indexer_search(temp_dirs, mock_ollama_client):
    """Test searching indexed documents."""
    indexer = DocIndexer(
        temp_dirs,
        use_ollama=True,
        ollama_client=mock_ollama_client,
    )

    doc_service = DocService(Path("/tmp"), temp_dirs)

    # Index a document
    segments = [
        {"segment_id": "s1", "text": "Python is a programming language."},
    ]
    indexer.index_document("test_doc", segments, doc_service)

    # Search
    results = indexer.search("programming", top_n=5)

    assert len(results) > 0


def test_doc_indexer_save_load(temp_dirs, mock_ollama_client):
    """Test saving and loading index."""
    indexer = DocIndexer(
        temp_dirs,
        use_ollama=True,
        ollama_client=mock_ollama_client,
    )

    doc_service = DocService(Path("/tmp"), temp_dirs)

    segments = [{"segment_id": "s1", "text": "Test content"}]
    indexer.index_document("test_doc", segments, doc_service)

    # Create new indexer and load
    indexer2 = DocIndexer(
        temp_dirs,
        use_ollama=True,
        ollama_client=mock_ollama_client,
    )

    stats = indexer2.get_stats()
    assert stats["total_segments"] > 0

