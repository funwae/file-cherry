# System Architecture

## Component Overview

1. **OS Layer**
   - Ubuntu Server minimal or similar.
   - SquashFS read-only root partition.
   - Data partition (exFAT/ext4) mounted at `/data`.

2. **Data Directories** (under `/data`)
   - `inputs/`
   - `outputs/`
   - `config/`
   - `logs/`
   - `runtime/` (internal caches, indices)

3. **Core Services**

- **Orchestrator Service** (Python):
  - main controller for jobs.
  - interacts with:
    - Ollama HTTP API
    - ComfyUI HTTP API
    - Document Indexer
  - manages state machine per job.

- **Ollama Service**:
  - runs local models (e.g. LLaMA-based).
  - accessible via HTTP on localhost.
  - provides:
    - conversational interface
    - tool-calling style responses for orchestrator.

- **ComfyUI Service**:
  - headless ComfyUI running as a server.
  - pipelines stored under `/data/config/comfy/pipelines/`.
  - orchestrator can:
    - load templates
    - modify nodes/parameters
    - execute graphs.

- **Document Processing Service**:
  - handles text extraction, embedding, indexing, retrieval.
  - interacts with orchestrator via RPC or message queue.

- **UI Layer**:
  - simple web UI served on `localhost:3000`.
  - kiosk browser (or TUI) on boot.

4. **Message Bus / Coordination**

- For v1, a **simple approach**:
  - orchestrator as central coordinator, calling services via HTTP.
  - jobs stored as JSON manifests under `/data/runtime/jobs/`.
- Future: optional queue (Redis/SQLite-backed) for concurrency.

## Data Flow (Happy Path)

1. On boot:
   - `/dev/data` mounted to `/data`.
   - orchestrator scans `/data/inputs/` and builds a preliminary job inventory (file list, types, sizes).
   - UI starts and connects to orchestrator.

2. User session:
   1. User sees list of detected file types (images, docs, audio, etc.).
   2. UI prompts:
      > "What do you want to do with these files?"
   3. UI sends:
      - file inventory
      - user's natural language request
      to orchestrator.

3. Planning:
   - Orchestrator sends a **planning prompt** to Ollama:
     - includes file list and user intent.
     - instructs model to choose operations from a tool schema:
       - `IMAGE_PIPELINE`, `DOC_ANALYSIS`, `MIXED_REPORT`, etc.
   - Ollama returns a structured plan (JSON-like):
     - steps, required services, parameters, target output structure.

4. Execution:
   - Orchestrator writes a job manifest in `/data/runtime/jobs/<id>.json`.
   - For each step:
     - calls ComfyUI / doc service.
     - monitors progress.
     - streams updates to UI.
   - Outputs are written to:
     - `/data/outputs/<job-id>/...`.

5. Completion:
   - Orchestrator marks job as `completed` in manifest.
   - UI shows a summary:
     - "X images processed"
     - "Y reports created"
     - location of outputs.

6. Shutdown:
   - User powers down.
   - USB now contains:
     - unchanged inputs unless auto-archived
     - new outputs
     - logs/manifests for reproducibility.

## Error Handling

- Job-level state: `pending`, `running`, `failed`, `completed`, `partial`.
- On failure:
  - orchestrator logs structured error.
  - UI shows human-readable explanation + suggestion (e.g. "one PDF was corrupt").
- Partial success allowed:
  - some files may succeed while others fail; results still accessible.

## Extensibility

- New services can be added via:
  - registration in `config/services.yaml`
  - new tool types exposed to Ollama in planning prompt.
- For each new capability:
  - define a **tool schema** (name, params, expected outputs)
  - implement mapping from tool invocations to actual service calls.

