# FileCherry Developer Workflows (Advanced)

This doc describes **day-to-day workflows** for working on FileCherry from Ubuntu (or WSL), with Cursor as your main IDE.

## 1. Repo Layout (Recap)

```text
filecherry/
  apps/
    ui/                # Next.js app
  src/
    orchestrator/      # Python orchestrator
    services/          # helpers for doc processing, comfy client, etc.
  tools/
    build_iso.sh       # build bootable ISO image
    network-doctor.sh  # diagnose networking
  docs/
  dev-data/            # local simulated /data
```

## 2. Daily Flow: "Change → Test → Commit"

### 2.1 Start Services

In three terminals or tmux panes:

1. **Ollama** (if not already as systemd service):
   ```bash
   ollama serve
   ```
2. **ComfyUI** (dev mode):
   ```bash
   cd /opt/ComfyUI
   source venv/bin/activate
   python main.py --listen 0.0.0.0 --port 8188
   ```
3. **FileCherry Orchestrator + UI** (from repo root):
   ```bash
   export FILECHERRY_DATA_DIR=$PWD/dev-data
   source .venv/bin/activate
   python -m src.orchestrator.main
   ```
   In another terminal:
   ```bash
   cd apps/ui
   npm run dev
   ```

### 2.2 Drop Test Files

```bash
mkdir -p dev-data/inputs
cp tests/fixtures/* dev-data/inputs/
```

Then open `http://localhost:3000` and run one job.

## 3. Using Cursor Effectively

### 3.1 "Narrate the Workflow"

When you ask Cursor's AI for help, **narrate the workflow**:

> "You are helping me build a bootable AI appliance on Ubuntu with a Python orchestrator and Next.js UI. The repo is filecherry/. The data dir is dev-data/, simulating /data on a USB."

This primes it to reason about the repo holistically instead of as isolated files.

### 3.2 Refactor Passes

Use Cursor's "Edit with AI" / "Chat" to:

1. Generate pure-Python utilities in `src/services/`.
2. Then ask it to create `tests/test_xyz.py` for each new utility.
3. Finally, wire them into `src/orchestrator/main.py`.

### 3.3 Debugging from Cursor

* Set breakpoints in `src/orchestrator/main.py`.
* Use a `launch.json` (VS Code compatible) to run with debug:
  ```jsonc
  {
    "configurations": [
      {
        "name": "Orchestrator",
        "type": "python",
        "request": "launch",
        "program": "src/orchestrator/main.py",
        "env": {
          "FILECHERRY_DATA_DIR": "${workspaceFolder}/dev-data"
        }
      }
    ]
  }
  ```
* Attach debugger, then use the web UI to trigger a job.

## 4. Workflow: "New Tool / Pipeline"

Example: adding a new **image pipeline** called `photo_collage`.

1. Create schema in `config/comfy/pipelines/photo_collage.yaml`.
2. Create ComfyUI workflow JSON in `/data/config/comfy/pipelines/photo_collage.json` (dev-data for dev).
3. Add a new `tool` descriptor in orchestrator's tool registry:
   * `src/orchestrator/tools/image_pipeline.py`.
4. Add unit tests for the new tool.
5. Run dev job that exercises only that tool.

## 5. Workflow: "LLM Prompt Change"

When adjusting planner prompts:

1. Create a new `prompt config` file:
   * `config/llm/planner_prompt.md`
2. Have orchestrator read prompt text from there.
3. For experiments:
   * create versions `planner_prompt_v2.md`, `v3`, etc.
   * toggle via `config/appliance.yaml`.

Add a simple environment variable override:

```bash
export FILECHERRY_PLANNER_PROMPT=config/llm/planner_prompt_v2.md
```

## 6. Workflow: "Build New ISO & Test"

1. Make sure tests pass:
   ```bash
   pytest
   ```
2. Run `tools/build_iso.sh` (see [ISO Build Script](19_iso_build_script.md)):
   ```bash
   sudo bash tools/build_iso.sh
   ```
3. Flash ISO to a USB (see [Deployment Guide](15_deployment_guide.md)).
4. Boot in a VM or spare machine and validate.

## 7. Workflow: "Support / Bug Report"

When someone reports "it doesn't work":

1. Ask them to run (on the appliance):
   ```bash
   sudo bash /opt/filecherry/tools/network-doctor.sh
   ```
   and send you the output.
2. Ask for the latest job manifest:
   ```bash
   ls /data/outputs
   cat /data/outputs/<job-id>/manifest.json
   ```
3. Reproduce locally with the same inputs (if possible).

## 8. Naming & Branch Strategy

* `main` – stable.
* `dev` – next minor version.
* Feature branches: `feature/comfy-pipeline-xyz`, `feature/doc-index-v2`, etc.

Use semantic-ish tags for OS images:

* `v0.1.0-dev1`, `v0.1.0-dev2`, etc.

