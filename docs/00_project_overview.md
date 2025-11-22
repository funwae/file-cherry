# FileCherry – Project Overview

## Elevator Pitch

FileCherry is a bootable AI appliance on a stick.

- On **Mac/Windows**: plug in the USB and it appears as a normal drive with:
  - `inputs/`  — drop in any files you want the AI to work on
  - `outputs/` — pick up processed results later
  - `config/`  — optional advanced configuration

- When you **boot a PC from the USB**, it starts a minimal Linux environment that:
  - mounts the same data partition
  - runs **Ollama** as the main conversation/agent brain
  - runs **ComfyUI** and document-processing pipelines as tools
  - shows a dead-simple UI:
    > "What do you want to do with these files?"

The system then:
- inspects everything in `inputs/`
- plans a sequence of operations (image pipelines, document analysis, mixed workflows)
- executes them automatically
- writes all results into `outputs/` (with clear subfolders and manifests)

The user can then:
- shut down
- plug the USB back into any Mac/PC
- copy results from `outputs/` into their usual environment.

## Core Capabilities

- **File-driven workflow**: all work is defined by what's in `inputs/`.
- **Conversational planning via Ollama**:
  - user specifies their intent in plain language
  - agent chooses appropriate pipelines/tools.
- **ComfyUI image workflows**:
  - generation, enhancement, style transfer, upscaling, etc.
  - pipelines can be auto-modified by the agent.
- **Long-form LLM document work**:
  - ingestion and indexing of all text-like files in `inputs/`
  - semantic search, clustering, and subject-wise compilation
  - question answering and reporting
  - writes structured outputs into `outputs/`.
- **Offline-first**:
  - everything runs locally; network is optional.
- **Future: app-build mode**:
  - take processed content and autogenerate:
    - `docs/` + app skeleton
    - push to GitHub (once linked)
    - ready for tools like Claude Code / Codex / Cursor to build from.

## Non-Goals (for initial versions)

- Not a general-purpose desktop OS.
- Not a multi-user network service.
- Not a full ComfyUI GUI for power users (we use ComfyUI as an engine).
- Not a replacement for full-featured MLOps platforms.

## High-Level Architecture

- **OS Layer**: Ubuntu-based live system with two main partitions:
  - read-only OS image
  - read/write data partition (inputs/outputs/config/logs).
- **Core Services**:
  - Orchestrator Service (Python)
  - Ollama Service
  - ComfyUI Service
  - Document Indexer & Retrieval service
  - Simple Web/TUI UI.
- **Data Model**: jobs based on scan of `inputs/`, with manifests and result bundles in `outputs/`.

See [System Architecture](02_system_architecture.md) for details.

## Documentation Structure

This documentation is organized into the following sections:

- [Product Vision](01_product_vision.md) - Problem space, personas, user stories
- [System Architecture](02_system_architecture.md) - Components, services, data flow
- [OS Image and Boot](03_os_image_and_boot.md) - Partition layout, boot process, systemd
- [Storage and File Layout](04_storage_and_file_layout.md) - `/data` structure, inputs/outputs/config
- [LLM Orchestration](05_llm_orchestration.md) - Ollama planning, tool schemas, prompts
- [ComfyUI Integration](06_comfyui_integration.md) - Pipeline schemas, ComfyUI API integration
- [Document Processing](07_document_processing.md) - Extraction, indexing, query/compile tools
- [UI/UX Specification](08_ui_ux_spec.md) - Screen flows, copy, error handling
- [Security and Privacy](09_security_and_privacy.md) - Local-first, token handling, logging
- [Telemetry and Logging](10_telemetry_and_logging.md) - Log formats, manifests, debugging
- [Automation and Future Expansion](11_automation_and_future_expansion.md) - App-build mode, GitHub integration
- [Developer Guide](12_developer_guide.md) - Dev setup, Cursor workflows, Ubuntu/WSL
- [Testing Strategy](13_testing_strategy.md) - Unit/integration/e2e/OS tests
- [Hardware Profiles](14_hardware_profiles.md) - Hardware tiers (thin client to GPU rig)
- [Deployment Guide](15_deployment_guide.md) - Manual deployment, USB flashing
- [Networking Guide](16_howtogetworking.md) - Networking cookbook, service debugging
- [Developer Workflows](17_developer_workflows.md) - Day-to-day dev patterns
- [Deployment Automation](18_deployment_automation.md) - ISO build automation
- [ISO Build Script](19_iso_build_script.md) - `tools/build_iso.sh` specification
- [USB Duplication Guide](20_usb_duplication_guide.md) - USB cloning procedures
- [Network Doctor Script](21_network_doctor_script.md) - `tools/network-doctor.sh` specification
- [Implementation Phases](PHASES.md) - Detailed implementation roadmap

