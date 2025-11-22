# Product Vision

## Problem Space

Typical small businesses:
- have scattered files (photos, PDFs, exports, notes) and no AI pipeline
- are intimidated by complex UIs, configuration, or "prompt engineering"
- often have weak or unreliable internet
- need a **tool, not a platform**.

At the same time, builders like us:
- can define very powerful image + document workflows
- but deploying them in a way Joe/Jo Manager can actually use is hard.

## Vision

> "Files in, value out. No settings, no accounts, no drama."

FileCherry should feel like:
- a **physical productivity device** (like a scanner or label printer)
- that just happens to be powered by state-of-the-art AI.

Key principles:

1. **Zero intimidation**
   - The UI never shows scary terms.
   - The user always sees exactly one next step.

2. **File-centric mental model**
   - Everything is "drop files into `inputs/` → boot → pick up results from `outputs/`".
   - There is no need to understand models, graphs, or embeddings.

3. **Conversational intent**
   - Ollama is the translator between human intent and pipelines.
   - Users describe outcomes; the system decides how.

4. **Offline-first, cloud-optional**
   - It must be fully usable with no network.
   - Optional cloud extensions (bigger models, GitHub pushes) are strictly opt-in.

5. **Composable building blocks**
   - Internally: modular components (image pipeline, doc pipeline, summarizer, indexer).
   - Externally: business-specific "presets" are just configuration + prompt templates.

## Primary Personas

1. **"Operations Owner"** (non-technical manager)
   - Wants repetitive tasks (e.g., car-photo cleanup, product description drafts) to just work.
   - Main interaction: dropping files, answering one question, collecting outputs.

2. **"AI Implementer"** (you / advanced user)
   - Comfortable with Python and configs.
   - Designs and refines pipelines.
   - Rarely interacts with the UI, mostly with configs and logs.

3. **"Developer/Partner"** (future ecosystem)
   - Builds packs/recipes for specific industries.
   - Ships zip files that users drop into `config/` to get new capabilities.

## Core User Stories

- As an **operations owner**, I want to:
  - drop photos into `inputs/`, boot, say "make dealership-ready car photos", and get cleaned images without further thought.
  - hand the stick to my staff and trust that they can't break anything.

- As an **AI implementer**, I want to:
  - define new workflows by writing Python modules + YAML, without modifying the OS image.
  - inspect logs and manifests to debug pipelines.

- As a **developer/partner**, I want to:
  - package my app idea (prompts, pipelines, templates) into one folder.
  - test it on my machine with the same USB pattern as end users.

## Success Criteria

- A non-technical person can:
  - read a 1-page quickstart
  - successfully complete a job from scratch in under 10 minutes.

- A technical implementer can:
  - add a new workflow without reflashing the OS
  - extend only in `config/` and `pipelines/`.

- The device can:
  - run fully offline once models are installed
  - recover gracefully from power loss or mid-run stops (idempotent job design).

