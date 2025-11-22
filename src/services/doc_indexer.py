"""
Document indexing service.

Creates vector embeddings and indexes documents for semantic search.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class DocumentIndex:
    """Vector index for document segments."""

    def __init__(self, index_dir: Path):
        """Initialize document index."""
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.embeddings_file = self.index_dir / "embeddings.pkl"
        self.metadata_file = self.index_dir / "metadata.json"

        self.embeddings: Optional[np.ndarray] = None
        self.metadata: List[Dict] = []

    def load(self):
        """Load index from disk."""
        if self.embeddings_file.exists() and self.metadata_file.exists():
            try:
                with open(self.embeddings_file, "rb") as f:
                    self.embeddings = pickle.load(f)

                with open(self.metadata_file, "r") as f:
                    self.metadata = json.load(f)

                logger.info(f"Loaded index with {len(self.metadata)} segments")
            except Exception as e:
                logger.error(f"Error loading index: {e}")
                self.embeddings = None
                self.metadata = []

    def save(self):
        """Save index to disk."""
        if self.embeddings is not None and self.metadata:
            try:
                with open(self.embeddings_file, "wb") as f:
                    pickle.dump(self.embeddings, f)

                with open(self.metadata_file, "w") as f:
                    json.dump(self.metadata, f, indent=2)

                logger.info(f"Saved index with {len(self.metadata)} segments")
            except Exception as e:
                logger.error(f"Error saving index: {e}")

    def add_segments(self, embeddings: np.ndarray, metadata: List[Dict]):
        """Add segments to index."""
        if self.embeddings is None:
            self.embeddings = embeddings
            self.metadata = metadata
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])
            self.metadata.extend(metadata)

    def search(self, query_embedding: np.ndarray, top_n: int = 5) -> List[Dict]:
        """Search for similar segments."""
        if self.embeddings is None or len(self.metadata) == 0:
            return []

        # Compute cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top N indices
        top_indices = np.argsort(similarities)[::-1][:top_n]

        results = []
        for idx in top_indices:
            results.append(
                {
                    **self.metadata[idx],
                    "similarity": float(similarities[idx]),
                }
            )

        return results


class DocIndexer:
    """Indexes documents with embeddings for semantic search."""

    def __init__(
        self,
        runtime_dir: Path,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        embedding_model: str = "all-MiniLM-L6-v2",
        use_ollama: bool = False,
        ollama_client: Optional[OllamaClient] = None,
    ):
        """Initialize document indexer."""
        self.runtime_dir = Path(runtime_dir)
        self.index_dir = self.runtime_dir / "doc-index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model_name = embedding_model
        self.use_ollama = use_ollama
        self.ollama_client = ollama_client

        # Initialize embedding model
        self.embedding_model = None
        if not use_ollama and SentenceTransformer is not None:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info(f"Loaded embedding model: {embedding_model}")
            except Exception as e:
                logger.warning(f"Could not load embedding model {embedding_model}: {e}")
                logger.info("Falling back to Ollama embeddings")
                self.use_ollama = True

        # Initialize index
        self.index = DocumentIndex(self.index_dir)
        self.index.load()

        logger.info(f"DocIndexer initialized - chunk_size={chunk_size}, overlap={chunk_overlap}")

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts."""
        if self.use_ollama and self.ollama_client:
            return self._get_ollama_embeddings(texts)
        elif self.embedding_model:
            return self.embedding_model.encode(texts, show_progress_bar=False)
        else:
            raise RuntimeError("No embedding method available")

    def _get_ollama_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings using Ollama API."""
        if not self.ollama_client:
            raise RuntimeError("Ollama client not available")

        embeddings = []
        for text in texts:
            try:
                # Use Ollama embeddings API
                response = self.ollama_client._request(
                    "POST",
                    "/api/embeddings",
                    json={"model": "phi3:mini", "prompt": text},
                )
                embedding = np.array(response.get("embedding", []))
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error getting Ollama embedding: {e}")
                # Fallback to zero vector
                embeddings.append(np.zeros(384))  # Default size

        return np.array(embeddings)

    def index_document(
        self, doc_id: str, segments: List[Dict], doc_service
    ) -> int:
        """
        Index a document's segments.

        Args:
            doc_id: Document identifier
            segments: List of segment dicts with 'text' field
            doc_service: DocService instance for chunking

        Returns:
            Number of chunks indexed
        """
        all_chunks = []
        all_metadata = []

        for segment in segments:
            text = segment.get("text", "")
            if not text:
                continue

            # Chunk the segment text
            chunks = doc_service.chunk_text(
                text, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )

            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"{segment.get('segment_id', 's1')}_c{chunk_idx}"
                all_chunks.append(chunk)
                all_metadata.append(
                    {
                        "doc_id": doc_id,
                        "segment_id": segment.get("segment_id", ""),
                        "chunk_id": chunk_id,
                        "text": chunk,
                        "page": segment.get("page"),
                        "heading": segment.get("heading"),
                    }
                )

        if not all_chunks:
            return 0

        # Get embeddings
        try:
            embeddings = self._get_embeddings(all_chunks)
            self.index.add_segments(embeddings, all_metadata)
            self.index.save()

            logger.info(f"Indexed {len(all_chunks)} chunks from {doc_id}")
            return len(all_chunks)
        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            return 0

    def search(self, query: str, top_n: int = 5) -> List[Dict]:
        """
        Search for similar segments.

        Args:
            query: Search query text
            top_n: Number of results to return

        Returns:
            List of matching segments with metadata
        """
        try:
            query_embedding = self._get_embeddings([query])[0]
            results = self.index.search(query_embedding, top_n=top_n)
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get index statistics."""
        return {
            "total_segments": len(self.index.metadata) if self.index.metadata else 0,
            "index_dir": str(self.index_dir),
            "embedding_model": self.embedding_model_name,
            "use_ollama": self.use_ollama,
        }

