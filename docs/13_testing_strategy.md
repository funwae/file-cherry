# FileCherry Testing Strategy

## 1. Testing Goals

We want FileCherry to be:

- predictable and deterministic where it matters
- resilient to weird inputs
- easy to regression-test despite using non-deterministic models.

Strategy = layer tests:

1. **Pure code** (unit tests)
2. **Service integration** (with Ollama/ComfyUI mocked or in "test mode")
3. **End-to-end** (job from `inputs/` → `outputs/` in a controlled environment)
4. **OS-level** (bootable image smoke tests).

## 2. Unit Tests

### 2.1 Targets

- File inventory & type detection
- Job manifest creation and updates
- Plan parsing/validation (LLM JSON → internal step objects)
- ComfyUI and doc-service client wrappers
- Config loading and validation.

### 2.2 Tools

- `pytest` for Python tests.
- `pytest-mock` / `unittest.mock` for mocking.
- `coverage.py` for coverage.

Example layout:

```text
src/
  orchestrator/
tests/
  test_inventory.py
  test_plan_parser.py
  test_manifest_store.py
```

### 2.3 Example: Plan Validation

* Provide sample JSON from planner.
* Validate error when required fields missing.
* Validate mapping from JSON to internal `Step` objects.

## 3. Integration Tests

### 3.1 Ollama Integration

Because Ollama is heavy, we distinguish:

* **Mock mode**: default for CI
* **Real mode**: for local dev with GPU/CPU models.

**Mock mode**:

* Provide a small HTTP stub:
  * intercepts `/api/chat` requests
  * returns canned JSON plans/data.

**Real mode**:

* Use a tiny model (e.g. `phi-2` or similar) for budget tests.
* Options:
  * deterministic prompts and temperature=0
  * snapshot-based assertions (loosely checks shape and key phrases).

### 3.2 ComfyUI Integration

Again: mock vs real.

**Mock mode**:

* Replace ComfyUI client with a fake that:
  * writes placeholder images.
  * logs call parameters.

**Real mode**:

* Use a small pipeline with minimal VRAM usage.
* Assertions:
  * `outputs/.../images` has expected number of files.
  * manifests link them correctly.

### 3.3 Doc Processing Integration

* Use sample PDFs, DOCX, TXTs.
* Assert:
  * segments extracted correctly (page numbers, etc).
  * index built and query returns relevant segments.

## 4. End-to-End Tests

### 4.1 Dev "Simulated Appliance" Test

Use `dev-data/` as `/data/`:

1. Populate `dev-data/inputs/` with known fixture set:
   * 3 images
   * 2 PDFs.
2. Start orchestrator + doc/image services (mock or real).
3. Use a CLI test harness:

```bash
FILECHERRY_DATA_DIR=dev-data python tools/run_e2e_job.py \
  --intent "Clean photos and summarize docs"
```

4. Assert:
* exactly one job manifest in `outputs/`.
* expected output directories exist.
* manifest statuses are `completed`.

### 4.2 API/Browser Tests

Optional:

* Use `playwright` or `cypress` to:
  * open `http://localhost:3000`
  * simulate user typing & clicks
  * verify job progress UI updates.

## 5. OS & USB Image Tests

Once we have a bootable image:

### 5.1 QEMU/VM Boot Test

* Spin up the ISO/IMG in QEMU/KVM.
* Use cloud-init or a scripted boot to:
  * mount a virtual disk as `/data`.
  * copy fixture files into `inputs/`.
  * script keyboard input (or run CLI mode) to simulate a job.

This mirrors the custom live-USB testing patterns described in Ubuntu's LiveCD customization docs, which use chrooted environments and QEMU to validate images before flashing.

### 5.2 Smoke Checks

Check:

* `systemctl status filecherry-orchestrator`
* `systemctl status ollama`
* `systemctl status comfyui`
* `curl http://localhost:3000/healthz`
* `ls /data` (verify inputs/outputs/config/logs/runtime).

### 5.3 Regression Matrix

After major changes, run:

* e2e tests on:
  * *no GPU* VM
  * *GPU* host
* and record performance numbers.

## 6. CI Considerations

### 6.1 What CI Runs

In GitHub Actions / other CI:

* Unit tests (fast).
* Integration tests in mock mode.
* Linting (`ruff`, `black`, `mypy`).
* UI tests (headless Next.js build).

### 6.2 What CI Doesn't Run (At First)

* Full ComfyUI / SDXL flows (too heavy for free runners).
* GPU-specific tests.

Instead, maintain a **manual test checklist** for GPU hosts.

## 7. Test Data Management

* Keep fixtures small and synthetic:
  * small placeholder images
  * trimmed PDFs.
* Store them under `tests/fixtures/`.
* No real customer data in the repo.

## 8. Developer Workflow

1. Write unit tests alongside new orchestrator features.
2. Add integration tests when introducing new tools/services.
3. Run e2e test locally before preparing a new OS image.
4. Tag a release only after all tests pass.

