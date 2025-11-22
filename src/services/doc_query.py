"""
Document query and compilation service.

Provides high-level query and compilation operations on indexed documents.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class DocQuery:
    """High-level document query and compilation operations."""

    def __init__(
        self,
        indexer,
        ollama_client: Optional[OllamaClient] = None,
        default_model: str = "phi3:mini",
    ):
        """Initialize document query service."""
        self.indexer = indexer
        self.ollama_client = ollama_client
        self.default_model = default_model

        logger.info("DocQuery initialized")

    def search(self, query: str, top_n: int = 5) -> List[Dict]:
        """
        Semantic search across documents.

        Args:
            query: Natural language search query
            top_n: Number of results to return

        Returns:
            List of matching segments with metadata
        """
        return self.indexer.search(query, top_n=top_n)

    def answer_question(
        self, question: str, doc_filters: Optional[List[str]] = None
    ) -> Dict:
        """
        Answer a question using document context.

        Args:
            question: Question to answer
            doc_filters: Optional list of doc_ids to limit search

        Returns:
            Dict with answer and supporting snippets
        """
        # Search for relevant context
        results = self.search(question, top_n=10)

        # Filter by doc_ids if specified
        if doc_filters:
            results = [r for r in results if r.get("doc_id") in doc_filters]

        if not results:
            return {
                "answer": "No relevant information found in documents.",
                "sources": [],
            }

        # Build context from top results
        context = "\n\n".join(
            [
                f"[From {r.get('doc_id', 'unknown')}, page {r.get('page', '?')}]:\n{r.get('text', '')}"
                for r in results[:5]
            ]
        )

        # Use LLM to generate answer
        if self.ollama_client:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on provided document context. Be concise and cite sources.",
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nContext:\n{context}\n\nAnswer the question based on the context above.",
                    },
                ]

                response = self.ollama_client.chat(
                    model=self.default_model, messages=messages, temperature=0.3
                )

                answer = response.get("message", {}).get("content", "Unable to generate answer.")

                return {
                    "answer": answer,
                    "sources": [
                        {
                            "doc_id": r.get("doc_id"),
                            "page": r.get("page"),
                            "segment_id": r.get("segment_id"),
                            "similarity": r.get("similarity"),
                        }
                        for r in results[:5]
                    ],
                }
            except Exception as e:
                logger.error(f"Error generating answer: {e}")
                return {
                    "answer": f"Error generating answer: {e}",
                    "sources": [],
                }
        else:
            # Fallback: return top result as answer
            return {
                "answer": results[0].get("text", "No answer available."),
                "sources": [
                    {
                        "doc_id": results[0].get("doc_id"),
                        "page": results[0].get("page"),
                    }
                ],
            }

    def compile_by_subject(
        self, subject: str, output_path: Optional[Path] = None
    ) -> str:
        """
        Compile documents by subject/topic.

        Args:
            subject: Subject or topic to compile
            output_path: Optional path to save compiled report

        Returns:
            Markdown report text
        """
        # Search for relevant segments
        results = self.search(subject, top_n=50)

        if not results:
            return f"# {subject}\n\nNo relevant documents found."

        # Group by document
        by_doc: Dict[str, List[Dict]] = {}
        for result in results:
            doc_id = result.get("doc_id", "unknown")
            if doc_id not in by_doc:
                by_doc[doc_id] = []
            by_doc[doc_id].append(result)

        # Build context
        context_sections = []
        for doc_id, segments in by_doc.items():
            doc_text = f"\n## From {doc_id}\n\n"
            for seg in segments[:10]:  # Limit per doc
                if seg.get("heading"):
                    doc_text += f"### {seg['heading']}\n\n"
                doc_text += f"{seg.get('text', '')}\n\n"
            context_sections.append(doc_text)

        context = "\n".join(context_sections)

        # Generate report using LLM
        if self.ollama_client:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "You are a technical writer. Create a well-structured report based on the provided document context. Use markdown formatting with clear sections and subsections. Include citations to source documents.",
                    },
                    {
                        "role": "user",
                        "content": f"Subject: {subject}\n\nCreate a comprehensive report on this subject based on the following document excerpts:\n\n{context}\n\nFormat as markdown with YAML frontmatter listing sources.",
                    },
                ]

                response = self.ollama_client.chat(
                    model=self.default_model, messages=messages, temperature=0.3
                )

                report_text = response.get("message", {}).get("content", "")

                # Add YAML frontmatter if not present
                if not report_text.startswith("---"):
                    sources = [
                        {
                            "doc": doc_id,
                            "pages": list(
                                set(
                                    seg.get("page")
                                    for seg in segments
                                    if seg.get("page") is not None
                                )
                            ),
                        }
                        for doc_id, segments in by_doc.items()
                    ]

                    frontmatter = {
                        "sources": sources,
                        "generated_at": datetime.utcnow().isoformat() + "Z",
                        "subject": subject,
                    }

                    import yaml

                    yaml_header = "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---\n\n"
                    report_text = yaml_header + report_text

            except Exception as e:
                logger.error(f"Error generating report: {e}")
                # Fallback: simple compilation
                report_text = self._simple_compilation(subject, by_doc)
        else:
            report_text = self._simple_compilation(subject, by_doc)

        # Save if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            logger.info(f"Saved compiled report to {output_path}")

        return report_text

    def _simple_compilation(self, subject: str, by_doc: Dict[str, List[Dict]]) -> str:
        """Simple compilation without LLM."""
        report = f"# {subject}\n\n"
        report += f"---\ngenerated_at: {datetime.utcnow().isoformat()}Z\n---\n\n"

        for doc_id, segments in by_doc.items():
            report += f"## From {doc_id}\n\n"
            for seg in segments[:10]:
                if seg.get("heading"):
                    report += f"### {seg['heading']}\n\n"
                report += f"{seg.get('text', '')}\n\n"

        return report

