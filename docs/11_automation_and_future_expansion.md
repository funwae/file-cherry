# Automation and Future Expansion

## Future: App Structure + GitHub Push

### Goal

From a rich `inputs/` set (docs, images, notes), automatically create:

- a `docs/` tree with Markdown specs
- optional starter code structure
- push to a linked GitHub repo
- ready for tools like Claude Code / Codex / Cursor to work with.

### High-Level Flow

1. **User Intent**

- Example request:
  > "Turn everything in `inputs/` into a spec and starter repo for a SaaS that sells car-photo cleanup as a service."

2. **Planning**

- Orchestrator asks Ollama for:
  - proposed directory structure
  - required doc types (`README`, `ARCHITECTURE`, `API`, etc.)
  - optional starter files (e.g. Next.js skeleton).

3. **Generation**

- LLM writes Markdown files describing:
  - product
  - user stories
  - system architecture
  - UI specs.
- Code skeleton generator:
  - uses templates + LLM to fill in boilerplate.
- Output stored in:

```text
outputs/<job-id>/app/
  docs/
  src/
  package.json
  ...
```

4. **GitHub Integration**

* If configured (token and repo in `config/github.yaml`):

  * `filecherry-github` service:

    * initializes repo (if needed)
    * commits generated contents
    * pushes to remote.

* Config example:

```yaml
github:
  enabled: true
  repo_url: "git@github.com:username/project.git"
  default_branch: "main"
```

5. **Handoff to Dev Tools**

* User opens repo in:

  * Claude Code / Cursor / VS Code with AI helpers.
* All specs and starter code ready for further iteration.

## Agentic Build-Out

Future evolution:

* Multi-turn autonomous agent:

  * iteratively refines specs based on its own code analysis.
* Tools:

  * `run_tests`
  * `lint`
  * `static_analysis`
* The agent:

  * loops until tests pass or budget exhausted.
  * logs each step to `outputs/<job-id>/build-log.md`.

## Extensibility Framework

Longer term, define a **plugin format**:

* `config/plugins/<plugin-name>/plugin.yaml`:

  * declares new tools (e.g. audio transcription, 3D pipeline).
* Corresponding code dropped into:

  * `/data/plugins/<plugin-name>/`.

Ollama planning prompt gets extended tool schema automatically.

## Next Conceptual Areas to Detail

Some additional .md docs that can be fleshed out as a second wave:

* `developer-guide.md` — for people implementing pipelines and plugins.
* `testing-strategy.md` — automated tests for orchestrator, pipelines, and OS image.
* `hardware-profiles.md` — recommended builds (Pi-like, NUC, full GPU tower) with performance expectations.
* `deployment-guide.md` — manufacturing / imaging process for many USBs.

Those can dive into test matrices, CI flows, and reproducible builds when you want to push this toward actual shipping hardware.

