# FileCherry Implementation Phases

This document outlines the phased implementation plan for FileCherry. Each phase builds on the previous one and should be completed before moving to the next.

## Phase 0: Documentation Structure & Repo Scaffolding

**Goal**: Organize all provided markdown specs into a coherent `docs/` folder and establish repo structure.

**Status**: ✅ Complete

**Tasks Completed**:
- Created `docs/` directory with all 22+ markdown files
- Created repo root structure (src/, apps/, tools/, tests/, dev-data/, etc.)
- Normalized documentation (removed duplication, fixed cross-references, ensured consistency)
- Created `docs/PHASES.md` implementation roadmap

**Deliverables**:
- Complete `docs/` folder with all documentation files
- Repo structure with empty directories
- `README.md` and `VERSION` file
- `docs/PHASES.md` implementation roadmap

---

## Phase 1: Orchestrator & Data Model Skeleton

**Goal**: Core orchestrator process with data inventory and manifest system.

**Tasks**:
1. Implement `src/orchestrator/main.py`:
   - FastAPI server on port 8000
   - Health endpoint `/healthz`
   - Job management endpoints

2. Implement `src/orchestrator/inventory.py`:
   - Scan `inputs/` directory recursively
   - Classify files by type (image, document, data, etc.)
   - Generate `runtime/inputs-inventory.json`

3. Implement `src/orchestrator/manifest.py`:
   - Job manifest creation (`outputs/<job-id>/manifest.json`)
   - Step tracking (pending, running, completed, failed)
   - Link inputs to outputs

4. Implement `src/orchestrator/job.py`:
   - Job state machine
   - Basic job execution loop (mock services for now)

5. Create `src/services/` structure:
   - `comfy_client.py` (stub)
   - `doc_service.py` (stub)
   - `ollama_client.py` (stub)

6. Add basic tests:
   - `tests/test_inventory.py`
   - `tests/test_manifest.py`

**Deliverables**:
- Working orchestrator that can scan inputs and create job manifests
- Mock job execution (no real services yet)
- Basic test coverage

---

## Phase 2: Ollama Planning Integration

**Goal**: Wire orchestrator to Ollama for conversational planning.

**Tasks**:
1. Implement `src/services/ollama_client.py`:
   - HTTP client for Ollama API (`http://127.0.0.1:11434`)
   - `chat()` method with tool schema
   - `plan()` method that formats planning prompt

2. Create `config/llm/planner_prompt.md`:
   - System prompt for planner
   - Tool schema definitions (IMAGE_PIPELINE, DOC_ANALYSIS, etc.)
   - Example outputs

3. Implement `src/orchestrator/planner.py`:
   - Load planner prompt template
   - Format prompt with file inventory + user intent
   - Parse JSON plan from Ollama response
   - Validate plan structure

4. Implement `src/orchestrator/tools/`:
   - `tool_registry.py` - Tool definitions
   - `image_pipeline.py` - IMAGE_PIPELINE tool (stub)
   - `doc_analysis.py` - DOC_ANALYSIS tool (stub)

5. Update orchestrator to:
   - Accept user intent from API
   - Call planner
   - Map plan steps to tool invocations
   - Execute tools (still stubbed)

6. Add tests:
   - `tests/test_ollama_client.py` (with mocks)
   - `tests/test_planner.py` (with sample JSON)

**Deliverables**:
- Orchestrator can call Ollama and get structured plans
- Plan validation and tool mapping working
- Tool execution still stubbed but wired up

---

## Phase 3: Document Processing Pipeline

**Goal**: Full document extraction, indexing, and analysis workflow.

**Tasks**:
1. Implement `src/services/doc_service.py`:
   - File type detection
   - Extractors: PDF (`pypdf`), DOCX (`python-docx`), TXT, HTML, CSV/JSON
   - Text segmentation (chunking with overlap)

2. Implement `src/services/doc_indexer.py`:
   - Embedding generation (local model or Ollama embeddings)
   - Vector index storage in `runtime/doc-index/`
   - Metadata tracking (doc_id, segment_id, pages)

3. Implement `src/services/doc_query.py`:
   - Semantic search (top-N segments)
   - Subject-based clustering
   - Q&A across documents

4. Implement `src/orchestrator/tools/doc_analysis.py`:
   - DOC_ANALYSIS tool implementation
   - Generate Markdown reports with YAML frontmatter
   - Write to `outputs/<job-id>/docs/`

5. Create `config/doc/indexer.yaml`:
   - Chunk size, overlap
   - Embedding model selection

6. Add tests:
   - `tests/test_doc_extraction.py`
   - `tests/test_doc_indexer.py`
   - `tests/fixtures/` with sample PDFs/DOCX

**Deliverables**:
- End-to-end: docs in `inputs/` → indexed → queryable → reports in `outputs/`
- Full document processing pipeline working

---

## Phase 4: ComfyUI & Image Pipelines

**Goal**: Image processing via ComfyUI headless server.

**Tasks**:
1. Implement `src/services/comfy_client.py`:
   - HTTP client for ComfyUI API (`http://127.0.0.1:8188`)
   - Graph upload/execution
   - Image download
   - Progress polling

2. Create pipeline schema system:
   - `config/comfy/pipelines/photo_cleanup.yaml` (schema)
   - `config/comfy/pipelines/photo_cleanup.json` (ComfyUI graph)
   - Pipeline loader that reads schema + graph

3. Implement `src/orchestrator/tools/image_pipeline.py`:
   - IMAGE_PIPELINE tool implementation
   - Map tool params to ComfyUI node parameters
   - Batch processing for multiple images
   - Write outputs to `outputs/<job-id>/images/`

4. Implement LLM-aware parameter tuning:
   - `config/comfy/semantic_controls.yaml` (e.g., "premium" → contrast 1.1)
   - Planner can suggest param adjustments
   - Orchestrator applies semantic controls

5. Add error handling:
   - ComfyUI unreachable → mark steps failed
   - Individual image failures → skip, continue others
   - Timeout handling

6. Add tests:
   - `tests/test_comfy_client.py` (with mock ComfyUI)
   - `tests/test_image_pipeline.py`

**Deliverables**:
- End-to-end: images in `inputs/` → ComfyUI processed → outputs in `outputs/`
- At least one working pipeline (photo cleanup)

---

## Phase 5: Web UI & UX Flow

**Goal**: Complete web interface matching UX spec.

**Tasks**:
1. Set up Next.js app in `apps/ui/`:
   - TypeScript + React
   - API routes for orchestrator communication

2. Implement screens:
   - **Intro Screen**: File inventory display, input textarea
   - **Plan Preview**: Show LLM plan, accept/edit buttons
   - **Job Progress**: Step-by-step progress, status updates
   - **Completion**: Summary, output locations, file browser

3. Implement API integration:
   - `GET /api/inventory` - Get inputs scan
   - `POST /api/jobs` - Submit job with intent
   - `GET /api/jobs/:id` - Get job status
   - `GET /api/jobs/:id/manifest` - Get manifest
   - WebSocket or polling for progress updates

4. Add error handling UI:
   - Human-readable error messages
   - Suggestions for common failures

5. Implement advanced UI toggle:
   - Controlled by `config/appliance.yaml` (`show_advanced`)
   - Model selection, pipeline options, logs view

6. Add styling:
   - Clean, minimal design
   - Responsive layout
   - Loading states

**Deliverables**:
- Full web UI on `localhost:3000`
- Complete user flow from file drop to results
- Advanced mode toggle working

---

## Phase 6: OS Image & Live USB

**Goal**: Bootable ISO with all services integrated.

**Tasks**:
1. Implement `tools/build_iso.sh`:
   - Download base Ubuntu ISO
   - Extract and chroot
   - Install dependencies (Ollama, ComfyUI, Node, Python)
   - Copy FileCherry code to `/opt/filecherry`
   - Set up systemd services
   - Repack ISO

2. Create systemd unit files in `docs/systemd/`:
   - `filecherry-orchestrator.service`
   - `filecherry-ui.service`
   - `comfyui.service`
   - `data.mount` (for `/data` partition)

3. Create `tools/prepare_usb.sh`:
   - Flash ISO to USB
   - Create data partition (exFAT)
   - Initialize `inputs/`, `outputs/`, `config/`, `logs/`, `runtime/`

4. Test in QEMU/KVM:
   - Boot ISO in VM
   - Verify all services start
   - Run network-doctor script
   - Execute test job

5. Document first-boot checklist

**Deliverables**:
- Working `build_iso.sh` script
- Bootable ISO that starts all services
- USB preparation script
- Tested in VM environment

---

## Phase 7: Appliance Polish

**Goal**: Production-ready hardening and observability.

**Tasks**:
1. Implement `tools/network-doctor.sh`:
   - Service health checks
   - Port scanning
   - Log tailing
   - Network diagnostics

2. Add comprehensive logging:
   - JSON-line format
   - Log rotation
   - Structured error codes

3. Security hardening:
   - Review file permissions
   - Validate no auto-mount of host drives
   - Token encryption for future GitHub integration

4. Performance optimization:
   - VRAM management for ComfyUI
   - Batch size tuning
   - Index caching strategies

5. Error recovery:
   - Idempotent job design
   - Partial success handling
   - Graceful degradation

6. Documentation updates:
   - Troubleshooting guide
   - Hardware-specific tuning notes

**Deliverables**:
- Network-doctor script working
- Production-grade logging and error handling
- Security review complete

---

## Phase 8: App-Build & GitHub Mode (Future)

**Goal**: Advanced mode for generating app specs and GitHub repos.

**Tasks**:
1. Implement app structure generator:
   - Read all `inputs/` content
   - Use LLM to generate:
     - `docs/` tree (README, ARCHITECTURE, API, UX)
     - Starter code skeleton (Next.js, FastAPI, etc.)

2. Implement GitHub integration:
   - `config/github.yaml` for tokens/repo
   - Git initialization and commit
   - Push to remote

3. Add new tool: `APP_BUILD`
   - Planner can suggest app generation
   - Orchestrator executes generator
   - Optionally pushes to GitHub

4. Gate behind config flag:
   - Only enabled if `config/appliance.yaml` allows
   - Clear opt-in required

**Deliverables**:
- App generation working
- GitHub integration (optional)
- Ready for handoff to AI coding assistants

---

## Key Implementation Notes

- **Wait for explicit "begin phase X" command** before starting any phase
- All phases build on previous phases
- Testing should be added incrementally with each phase
- Documentation should be updated as implementation progresses
- Use `dev-data/` for local development, `/data` for appliance mode

