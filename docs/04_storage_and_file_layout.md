# Storage and File Layout

## Data Root

All user-visible data lives under `/data` on the OS, and as the root of the USB when plugged into other machines.

```text
/data
  inputs/
  outputs/
  config/
  logs/
  runtime/
```

### `inputs/`

Purpose: user drops any files for processing.

Rules:

* Arbitrary folder structure allowed; system treats each top-level file/folder as candidate input.
* Supported types (initially):

  * Images: `.jpg`, `.jpeg`, `.png`, `.webp`, `.tiff`
  * Documents: `.pdf`, `.docx`, `.txt`, `.md`, `.html`, `.rtf`
  * Data: `.csv`, `.json`
  * Audio (future): `.wav`, `.mp3`
* On boot, orchestrator builds an **inventory**:

```jsonc
// /data/runtime/inputs-inventory.json
{
  "scanned_at": "...",
  "items": [
    {
      "path": "inputs/sales/2024-q1-report.pdf",
      "type": "document",
      "size_bytes": 123456
    },
    {
      "path": "inputs/cars/photo-001.jpg",
      "type": "image",
      "size_bytes": 345678
    }
  ]
}
```

### `outputs/`

Purpose: all produced artifacts.

Structure:

```text
outputs/
  <job-id>/
    manifest.json
    images/
    docs/
    misc/
```

* `job-id`:

  * `YYYYMMDD-HHMMSS-<short-random>`, e.g. `20251121-154230-8f3a`.
* `manifest.json`:

  * links each output to:

    * originating input(s)
    * pipeline used
    * parameters
    * timestamps
    * success/failure metadata.

Example manifest snippet:

```json
{
  "job_id": "20251121-154230-8f3a",
  "intent": "Clean up car photos and summarize PDFs",
  "steps": [
    {
      "name": "image_cleanup",
      "service": "comfyui",
      "inputs": ["inputs/cars/photo-001.jpg"],
      "outputs": ["outputs/20251121-154230-8f3a/images/photo-001-clean.jpg"]
    }
  ]
}
```

### `config/`

Configuration files, safe to edit by advanced users.

Suggested layout:

```text
config/
  appliance.yaml
  ollama/
    models.yaml
  comfy/
    pipelines/
      car_cleanup.json
      ...
  doc/
    indexer.yaml
    prompts.yaml
```

`appliance.yaml` example:

```yaml
appliance_name: FileCherry
default_llm_model: "phi3:mini"
allowed_models:
  - "phi3:mini"
  - "mistral-small"
ui:
  theme: "light"
  show_advanced: false
defaults:
  job_mode: "ask"   # ask | auto
```

### `logs/`

* Application logs, rotated:

  * `orchestrator.log`
  * `ollama.log`
  * `comfyui.log`
  * `doc-indexer.log`
* Each job gets a dedicated log file or entry correlated with job-id.

### `runtime/`

* Internal caches and indices.
* Examples:

  * `runtime/jobs/` — job manifests and state.
  * `runtime/doc-index/` — vector index files.
  * `runtime/tmp/` — scratch space.
* Can be safely deleted for reset (with documented consequences).

