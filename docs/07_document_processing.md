# Document Processing and Long-Form LLM Work

## Goals

- Index and analyze all **textual** content under `inputs/`.
- Support:
  - semantic search
  - subject-wise compilation
  - query-based summarization
  - cross-document reports.

## Ingestion

Supported types (initial):

- `.pdf`, `.docx`, `.txt`, `.md`, `.html`, `.rtf`, `.csv`, `.json`.

Pipeline:

1. File discovery (from inventory).
2. Type-specific extractor:
   - PDF: `pypdf` / `pdfminer`.
   - DOCX: `python-docx`.
   - HTML: strip tags, keep headings.
   - CSV/JSON: convert to human-readable table text where useful.
3. Produce unified segments:

```json
{
  "doc_id": "inputs/reports/2024-q1.pdf",
  "segments": [
    {
      "segment_id": "s1",
      "text": "First paragraph...",
      "page": 1
    }
  ]
}
```

4. Store raw extracted text under `/data/runtime/doc-raw/<hash>.json`.

## Indexing

* Use a local embedding model (e.g. smaller model via Ollama or separate library).
* Build vector index stored in `/data/runtime/doc-index/`.
* Metadata:

  * `doc_id`, `segment_id`, page numbers, headings.

Indexing parameters configurable in `config/doc/indexer.yaml`:

```yaml
chunk_size: 1024
chunk_overlap: 128
embedding_model: "local-embeddings-small"
```

## Query and Compilation

LLM supports document tasks via tools defined for orchestrator:

1. **Search Tool**

   * Input: natural language query.
   * Output: top-N segments.

2. **Compile by Subject Tool**

   * Input: subject/topic.
   * Steps:

     1. Search index for relevant segments.
     2. Cluster by subtopic (using embeddings or LLM).
     3. Ask LLM to write:

        * overview
        * sections per subtopic
        * citations back to original docs.
   * Output: Markdown report stored in `outputs/<job-id>/docs/subject-report.md`.

3. **Query Answering Tool**

   * Input: question and optional doc filters.
   * Output: direct answer + supporting snippets.

## Output Structure

For doc-focused jobs, produce:

```text
outputs/<job-id>/docs/
  summary-all.md
  by-subject/
    marketing.md
    operations.md
  qa/
    question-1.md
```

Each file begins with YAML frontmatter describing sources:

```md
---
sources:
  - doc: "inputs/reports/2024-q1.pdf"
    pages: [3,4,5]
generated_at: "2025-11-21T15:42:00Z"
---

# Q1 Sales Summary
...
```

## Performance & Limits

* Index size controlled via:

  * max file size
  * max total characters.
* For huge corpora:

  * chunk indexing across boots (resume from `runtime` state).
  * UI should show "X of Y docs indexed" progress.

## Safety

* If extraction fails for a file:

  * mark as skipped in manifest.
* If index is corrupted:

  * fall back to direct text scanning per job.

