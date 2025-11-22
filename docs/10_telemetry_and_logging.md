# Telemetry, Logging, and Observability

*(Telemetry here is local/system-level; remote telemetry is optional and off by default.)*

## Objectives

- Make development and troubleshooting easy.
- Provide enough visibility for power users.
- Avoid overwhelming non-technical users with noise.

## Logging Layers

1. **System Logs**
   - OS and services (`journalctl`).
   - Standard locations.

2. **Application Logs** (under `/data/logs/`)

- `orchestrator.log`
- `ollama.log`
- `comfyui.log`
- `doc-indexer.log`
- `ui.log`

Format (JSON lines recommended):

```json
{
  "timestamp": "2025-11-21T15:42:30Z",
  "level": "INFO",
  "component": "orchestrator",
  "job_id": "20251121-154230-8f3a",
  "message": "Starting ComfyUI pipeline photo_cleanup_v1 for 24 images."
}
```

## Job Manifests

* Primary source of truth for job status.
* Stored per job under `outputs/<job-id>/manifest.json`.
* Contains:

  * plan summary
  * step list
  * step statuses
  * errors (if any)
  * timing information.

## Debugging Tools

Command-line helpers:

* `filecherry-jobs`:

  * list recent jobs and statuses.
* `filecherry-job <job-id>`:

  * print manifest summary.
* `filecherry-logs <job-id>`:

  * tail log entries filtered by job.

## Local Telemetry Dashboard (Future)

* Optional small dashboard at `http://localhost:3000/admin`:

  * CPU/GPU usage
  * VRAM usage
  * number of files processed.
* Access gated behind `show_advanced` and maybe a simple password.

## Log Retention

* Configurable in `config/appliance.yaml`:

```yaml
logs:
  retention_days: 30
  max_size_mb: 512
```

* Simple log rotation scheme (size/time-based).
* Provide "Clear logs" button in advanced UI.

