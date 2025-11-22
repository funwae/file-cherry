<img src="cody.png" alt="Cody the Cherry Picker" height="250">

# FileCherry 🍒
_files in, cherries out_

FileCherry is a **bootable AI OS on a USB stick**.

You plug it in, dump your chaos into `inputs/`, boot from it, and a cartoon foreman named **Cody the Cherry Picker** runs your files through local AI (Ollama + image/doc pipelines), then hands you neat results in `outputs/`.

No SaaS, no login, no dashboard sprawl. Just a stick, a box, and a guy with too many cherries.

---

## What it does (for normal humans)

- Shows up as a normal drive on your Mac/PC:
  - You drag files into `inputs/`
  - Later you grab results from `outputs/`

- When you boot from it:
  - It scans what's in `inputs/`
  - Asks _"What do you want to do with these files?"_
  - Runs AI pipelines (images + docs) on the machine you booted
  - Drops everything in `outputs/<job-id>/`

That's the whole magic trick.

---

## What it does (for devs, but still in English)

- Live **Ubuntu-based** OS on a USB.

- `/data` partition (label `FILECHERRY_DATA`) with:
  - `inputs/`, `outputs/`, `config/`, `logs/`, `runtime/`

- A **Python orchestrator**:
  - Talks to **Ollama** for planning + summaries
  - Talks to **ComfyUI** for image pipelines
  - Writes job manifests + artifacts in `outputs/`

- A tiny **web UI** on `localhost:3000`:
  - "What do you want to do with these files?" text box
  - progress view
  - **Chat with Cody** panel for help and snark

You can hack all of this. The `docs/` folder is intentionally overkill.

---

## Cody, the cherry-powered foreman

Cody is:

- A cartoon in overalls with a mesh cap and a backpack of cherry sacks (files).

- The voice of the app:
  - UI copy
  - onboarding ("Cody's first job")
  - in-app `Chat with Cody` assistant (backed by Ollama)

Ask him things like:

- "Where did my outputs go?"
- "Why did that job fail?"
- "How should I structure inputs for car photos?"

He'll roast your filenames, not you.

---

## Quick dev poke (not the full appliance)

You want to just run the stack locally first:

```bash
git clone https://github.com/funwae/file-cherry.git
cd file-cherry

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

cd apps/ui
npm install
cd ../..

mkdir -p dev-data/{inputs,outputs,config,logs,runtime}
export FILECHERRY_DATA_DIR=$PWD/dev-data
```

Run orchestrator + UI (assuming Ollama & ComfyUI are already running):

```bash
# terminal 1
source .venv/bin/activate
python -m src.orchestrator.main

# terminal 2
cd apps/ui
npm run dev
```

Open `http://localhost:3000`, drop some files into `dev-data/inputs/`, and start yelling instructions at Cody.

---

## Building the USB thing (in one paragraph)

There's a script in `tools/build_iso.sh` that:

* takes a base Ubuntu ISO,
* injects FileCherry (orchestrator, UI, configs),
* **pre-installs phi3:mini model** (so it's ready to go on first boot),
* spits out a new ISO you can `dd` onto a USB,
* then you add a data partition labeled `FILECHERRY_DATA` with `inputs/` + `outputs/`.

Details live in `docs/15_deployment_guide.md` and friends. Read those before you nuke the wrong disk.

---

## Status / contributing

This is early. Expect sharp edges, TODOs with opinions, and overly honest comments.

Good PRs:

* new image pipelines (ComfyUI graphs)
* better doc processing / summarization flows
* smoother ISO/USB build flow
* anything that adds complexity **and** adds docs

If you just want to watch a cartoon cherry picker orchestrate an AI stack from a USB stick, that's valid too.
