"""
DOC_ANALYSIS tool implementation.

Analyzes documents for summarization, search, and compilation.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from ...services.doc_indexer import DocIndexer
from ...services.doc_query import DocQuery
from ...services.doc_service import DocService
from ...services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class DocAnalysisTool:
    """Tool for analyzing documents."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        runtime_dir: Optional[Path] = None,
        ollama_client: Optional[OllamaClient] = None,
    ):
        """Initialize document analysis tool."""
        # Get directories from environment or use defaults
        if data_dir is None:
            data_dir = Path(os.getenv("FILECHERRY_DATA_DIR", "/data"))
        if runtime_dir is None:
            runtime_dir = data_dir / "runtime"

        self.data_dir = Path(data_dir)
        self.runtime_dir = Path(runtime_dir)

        # Initialize services
        self.doc_service = DocService(self.data_dir, self.runtime_dir)
        self.indexer = DocIndexer(
            self.runtime_dir,
            chunk_size=1024,
            chunk_overlap=128,
            use_ollama=(ollama_client is not None),
            ollama_client=ollama_client,
        )
        self.query_service = DocQuery(
            self.indexer, ollama_client=ollama_client
        )

        logger.info("DocAnalysisTool initialized")

    def execute(
        self,
        query: str,
        input_paths: List[str],
        output_kind: str = "summary",
        job_id: str = None,
        manifest_manager=None,
    ) -> Dict:
        """
        Execute document analysis.

        Args:
            query: What to analyze or find
            input_paths: List of document file paths
            output_kind: Type of output (summary, qa, clustered_report)
            job_id: Job ID for tracking
            manifest_manager: Manifest manager for updating job state

        Returns:
            Dict with execution results
        """
        logger.info(f"Executing DOC_ANALYSIS: {output_kind} for {len(input_paths)} documents")

        outputs = []
        errors = []

        # Step 1: Extract text from all documents
        all_segments = []
        for input_path in input_paths:
            full_path = self.data_dir / input_path if not Path(input_path).is_absolute() else Path(input_path)

            try:
                result = self.doc_service.extract_text(str(full_path))
                if result.get("error"):
                    errors.append(f"{input_path}: {result['error']}")
                    continue

                segments = result.get("segments", [])
                all_segments.append((input_path, segments))

                # Index the document
                self.indexer.index_document(input_path, segments, self.doc_service)

            except Exception as e:
                error_msg = f"Error processing {input_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        # Step 2: Generate output based on output_kind
        output_dir = self.data_dir / "outputs" / job_id / "docs" if job_id else self.data_dir / "outputs" / "temp" / "docs"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            if output_kind == "summary":
                # Generate summary of all documents
                summary_text = self._generate_summary(query, all_segments)
                summary_path = output_dir / "summary-all.md"
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(summary_text)
                outputs.append(str(summary_path.relative_to(self.data_dir)))

            elif output_kind == "qa":
                # Answer questions
                answer = self.query_service.answer_question(query)
                qa_path = output_dir / "qa" / "question-1.md"
                qa_path.parent.mkdir(parents=True, exist_ok=True)

                qa_text = f"""---
question: "{query}"
generated_at: "{self._now_iso()}"
sources:
{self._format_sources(answer.get('sources', []))}
---

# Answer

{answer.get('answer', 'No answer available.')}
"""
                with open(qa_path, "w", encoding="utf-8") as f:
                    f.write(qa_text)
                outputs.append(str(qa_path.relative_to(self.data_dir)))

            elif output_kind == "clustered_report":
                # Compile by subject
                report_text = self.query_service.compile_by_subject(query)
                subject_safe = "".join(c for c in query if c.isalnum() or c in (" ", "-", "_")).strip()[:50]
                report_path = output_dir / "by-subject" / f"{subject_safe}.md"
                report_path.parent.mkdir(parents=True, exist_ok=True)

                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report_text)
                outputs.append(str(report_path.relative_to(self.data_dir)))

            else:
                # Default: semantic search
                results = self.query_service.search(query, top_n=10)
                search_path = output_dir / "search-results.md"

                search_text = f"""---
query: "{query}"
generated_at: "{self._now_iso()}"
results_count: {len(results)}
---

# Search Results

"""
                for idx, result in enumerate(results, 1):
                    search_text += f"""## Result {idx}

**Source:** {result.get('doc_id', 'unknown')} (page {result.get('page', '?')})
**Similarity:** {result.get('similarity', 0):.3f}

{result.get('text', '')}

---

"""
                with open(search_path, "w", encoding="utf-8") as f:
                    f.write(search_text)
                outputs.append(str(search_path.relative_to(self.data_dir)))

        except Exception as e:
            error_msg = f"Error generating output: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Update manifest if provided
        if manifest_manager and job_id:
            step_index = len(manifest_manager.load_manifest(job_id)["steps"])
            manifest_manager.update_step(
                job_id=job_id,
                step_index=step_index,
                status="completed" if not errors else "partial",
                outputs=outputs,
                error="; ".join(errors) if errors else None,
            )

        return {
            "tool": "DOC_ANALYSIS",
            "status": "completed" if not errors else "partial",
            "input_count": len(input_paths),
            "outputs": outputs,
            "errors": errors,
        }

    def _generate_summary(self, query: str, all_segments: List[tuple]) -> str:
        """Generate summary of documents."""
        # Build context from all segments
        context_parts = []
        for doc_id, segments in all_segments:
            doc_text = f"\n## {doc_id}\n\n"
            for seg in segments[:20]:  # Limit per doc
                doc_text += f"{seg.get('text', '')}\n\n"
            context_parts.append(doc_text)

        context = "\n".join(context_parts)

        # Use query service to generate summary
        if self.query_service.ollama_client:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "You are a technical writer. Create a concise summary based on the provided document content.",
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nCreate a summary based on the following documents:\n\n{context}",
                    },
                ]

                response = self.query_service.ollama_client.chat(
                    model=self.query_service.default_model,
                    messages=messages,
                    temperature=0.3,
                )

                summary = response.get("message", {}).get("content", "")
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
                summary = f"# Summary\n\nError generating summary: {e}"
        else:
            summary = f"# Summary\n\n{context[:1000]}..."

        # Add frontmatter
        sources = [{"doc": doc_id} for doc_id, _ in all_segments]
        frontmatter = f"""---
sources:
{self._format_sources(sources)}
generated_at: "{self._now_iso()}"
query: "{query}"
---

# Summary

{summary}
"""

        return frontmatter

    def _format_sources(self, sources: List[Dict]) -> str:
        """Format sources for YAML frontmatter."""
        import yaml

        return yaml.dump(sources, default_flow_style=False).strip()

    def _now_iso(self) -> str:
        """Get current time in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"
