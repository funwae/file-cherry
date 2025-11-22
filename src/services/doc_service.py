"""
Document processing service.

Handles text extraction from various document formats.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

logger = logging.getLogger(__name__)


class DocumentSegment:
    """Represents a segment of extracted text from a document."""

    def __init__(
        self,
        segment_id: str,
        text: str,
        page: Optional[int] = None,
        heading: Optional[str] = None,
    ):
        self.segment_id = segment_id
        self.text = text
        self.page = page
        self.heading = heading

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "segment_id": self.segment_id,
            "text": self.text,
        }
        if self.page is not None:
            result["page"] = self.page
        if self.heading:
            result["heading"] = self.heading
        return result


class DocService:
    """Service for document processing."""

    def __init__(self, data_dir: Path, runtime_dir: Path):
        """Initialize document service."""
        self.data_dir = Path(data_dir)
        self.runtime_dir = Path(runtime_dir)
        self.doc_raw_dir = self.runtime_dir / "doc-raw"
        self.doc_raw_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"DocService initialized - data_dir: {data_dir}")

    def _file_hash(self, file_path: Path) -> str:
        """Generate hash for a file."""
        return hashlib.sha256(str(file_path).encode()).hexdigest()[:16]

    def _save_extracted(self, doc_id: str, segments: List[DocumentSegment]) -> Path:
        """Save extracted segments to runtime directory."""
        hash_id = self._file_hash(Path(doc_id))
        output_file = self.doc_raw_dir / f"{hash_id}.json"

        data = {
            "doc_id": doc_id,
            "segments": [seg.to_dict() for seg in segments],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_file

    def extract_text(self, file_path: str) -> Dict:
        """
        Extract text from a document file.

        Args:
            file_path: Path to the document file

        Returns:
            Dict with doc_id and segments
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path_obj.suffix.lower()

        logger.info(f"Extracting text from {file_path} (type: {ext})")

        try:
            if ext == ".pdf":
                segments = self._extract_pdf(file_path_obj)
            elif ext == ".docx":
                segments = self._extract_docx(file_path_obj)
            elif ext in [".txt", ".md"]:
                segments = self._extract_text_file(file_path_obj)
            elif ext == ".html":
                segments = self._extract_html(file_path_obj)
            elif ext == ".csv":
                segments = self._extract_csv(file_path_obj)
            elif ext == ".json":
                segments = self._extract_json(file_path_obj)
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return {
                    "doc_id": str(file_path),
                    "segments": [],
                    "error": f"Unsupported file type: {ext}",
                }

            # Save extracted text
            self._save_extracted(str(file_path), segments)

            return {
                "doc_id": str(file_path),
                "segments": [seg.to_dict() for seg in segments],
            }

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return {
                "doc_id": str(file_path),
                "segments": [],
                "error": str(e),
            }

    def _extract_pdf(self, file_path: Path) -> List[DocumentSegment]:
        """Extract text from PDF file."""
        if PdfReader is None:
            raise ImportError("pypdf is not installed")

        segments = []
        reader = PdfReader(file_path)

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text.strip():
                segments.append(
                    DocumentSegment(
                        segment_id=f"s{page_num}",
                        text=text.strip(),
                        page=page_num,
                    )
                )

        return segments

    def _extract_docx(self, file_path: Path) -> List[DocumentSegment]:
        """Extract text from DOCX file."""
        if DocxDocument is None:
            raise ImportError("python-docx is not installed")

        segments = []
        doc = DocxDocument(file_path)

        current_heading = None
        current_text = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Check if this is a heading
            if para.style.name.startswith("Heading"):
                # Save previous segment if any
                if current_text:
                    segments.append(
                        DocumentSegment(
                            segment_id=f"s{len(segments) + 1}",
                            text="\n".join(current_text),
                            heading=current_heading,
                        )
                    )
                    current_text = []

                current_heading = text
                current_text.append(text)
            else:
                current_text.append(text)

        # Save last segment
        if current_text:
            segments.append(
                DocumentSegment(
                    segment_id=f"s{len(segments) + 1}",
                    text="\n".join(current_text),
                    heading=current_heading,
                )
            )

        return segments

    def _extract_text_file(self, file_path: Path) -> List[DocumentSegment]:
        """Extract text from plain text or markdown file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        segments = []
        for idx, para in enumerate(paragraphs, start=1):
            segments.append(
                DocumentSegment(
                    segment_id=f"s{idx}",
                    text=para,
                )
            )

        return segments

    def _extract_html(self, file_path: Path) -> List[DocumentSegment]:
        """Extract text from HTML file."""
        if BeautifulSoup is None:
            raise ImportError("beautifulsoup4 is not installed")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        soup = BeautifulSoup(content, "lxml")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract text
        text = soup.get_text()

        # Split into paragraphs
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        segments = []
        current_para = []
        for line in lines:
            if line:
                current_para.append(line)
            else:
                if current_para:
                    segments.append(
                        DocumentSegment(
                            segment_id=f"s{len(segments) + 1}",
                            text="\n".join(current_para),
                        )
                    )
                    current_para = []

        if current_para:
            segments.append(
                DocumentSegment(
                    segment_id=f"s{len(segments) + 1}",
                    text="\n".join(current_para),
                )
            )

        return segments

    def _extract_csv(self, file_path: Path) -> List[DocumentSegment]:
        """Extract text from CSV file."""
        import csv

        segments = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows = list(reader)

            if rows:
                # Header row
                header = ", ".join(rows[0])
                segments.append(
                    DocumentSegment(
                        segment_id="s1",
                        text=f"CSV Header: {header}",
                    )
                )

                # Data rows (limit to first 100 for readability)
                data_text = []
                for row in rows[1:101]:
                    data_text.append(", ".join(str(cell) for cell in row))

                if data_text:
                    segments.append(
                        DocumentSegment(
                            segment_id="s2",
                            text="CSV Data:\n" + "\n".join(data_text),
                        )
                    )

        return segments

    def _extract_json(self, file_path: Path) -> List[DocumentSegment]:
        """Extract text from JSON file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)

        # Convert JSON to readable text
        json_text = json.dumps(data, indent=2)

        segments = [
            DocumentSegment(
                segment_id="s1",
                text=f"JSON Content:\n{json_text}",
            )
        ]

        return segments

    def chunk_text(
        self, text: str, chunk_size: int = 1024, chunk_overlap: int = 128
    ) -> List[str]:
        """
        Split text into chunks with overlap.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for punct in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct != -1:
                        end = last_punct + len(punct)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - chunk_overlap
            if start >= len(text):
                break

        return chunks
