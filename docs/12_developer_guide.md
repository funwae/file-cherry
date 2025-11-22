# FileCherry Developer Guide

## 1. Overview

FileCherry is a bootable Ubuntu-based appliance that:

- uses a **read-only system partition** plus a **read/write data partition** (`/data`)

- runs **Ollama** as the LLM brain

- runs **ComfyUI** for image pipelines

- exposes a **simple web UI** on `localhost:3000`

- orchestrates jobs based on `inputs/` → `outputs/`.

This guide is for developing FileCherry in **Ubuntu** using **Cursor** (on bare metal Linux or via WSL2 from Windows).

## 2. Recommended Dev Setup

### 2.1 Host Options

You have three good options:

1. **Native Ubuntu workstation** (ideal).

2. **Ubuntu in WSL2 + Cursor on Windows**:

   - Install Cursor on Windows, then use the VS Code "Remote WSL" extension so Cursor attaches to the Ubuntu filesystem/processes inside WSL.

3. **Ubuntu VM** (VirtualBox, VMware, etc.) and point Cursor at a shared folder.

In all cases, aim for:

- 16GB+ RAM

- 50–100GB disk

- NVIDIA GPU if you want fast SD/ComfyUI development.

### 2.2 Base Packages

On your Ubuntu dev machine:

```bash
sudo apt update
sudo apt install -y git build-essential python3 python3-venv python3-pip \
  curl wget unzip zstd jq
```

Optional but useful:

```bash
sudo apt install -y htop nvtop net-tools tmux
```

### 2.3 Clone Repo

```bash
git clone https://github.com/your-org/filecherry.git
cd filecherry
```

(We'll assume root of repo is `filecherry/`.)

### 2.4 Python Env

Inside `filecherry/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

For local-only dev, requirements should include:

* `fastapi`, `uvicorn`
* `pydantic`
* `pytest`
* `httpx`
* `rich`
* document libs: `pypdf`, `python-docx`, etc.

## 3. Installing & Using Ollama in Dev

Follow the official instructions to install **Ollama** for Linux.

Key facts:

* Ollama runs an HTTP API on **port 11434** by default.
* It binds to `127.0.0.1` (loopback) by default; you can change this with `OLLAMA_HOST`.

After installation:

```bash
systemctl status ollama
ollama list          # see installed models
ollama pull phi3:mini   # example
```

For dev, we usually keep Ollama bound to `127.0.0.1` and let the orchestrator call it locally.

If you need network access (e.g. testing from another machine) see [Networking Guide](16_howtogetworking.md).

For debugging:

```bash
journalctl -u ollama --no-pager --since "5 minutes ago"
```

The official docs recommend `journalctl -u ollama --no-pager --follow` to tail logs live.

## 4. Installing & Running ComfyUI in Dev

Use a standard Ubuntu ComfyUI guide for a persistent dev install. Several reliable guides walk through installing to `/opt/ComfyUI`, setting up Python env, and configuring a **systemd** service.

For simple dev (no systemd yet):

```bash
cd /opt
sudo git clone https://github.com/comfyanonymous/ComfyUI.git
sudo chown -R "$USER":"$USER" ComfyUI
cd ComfyUI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py --listen 0.0.0.0 --port 8188
```

Make sure it works by opening `http://localhost:8188` in a browser.

Later, we'll run ComfyUI headless via systemd; see [Deployment Guide](15_deployment_guide.md).

## 5. Running the Orchestrator + UI in Dev

Inside the `filecherry/` repo:

* The orchestrator lives at `src/orchestrator/`.
* The web UI lives at `apps/ui/` (Next.js or similar).

### 5.1 Data Dir (Dev)

On dev, we use a **local folder** to simulate the USB data partition:

```bash
mkdir -p dev-data/{inputs,outputs,config,logs,runtime}
```

Set env var for orchestrator:

```bash
export FILECHERRY_DATA_DIR=$PWD/dev-data
```

### 5.2 Start Services (Dev)

In two terminals (or use `tmux`):

**Terminal A – Orchestrator**

```bash
source .venv/bin/activate
python -m src.orchestrator.main
```

**Terminal B – UI**

If it's Next.js:

```bash
cd apps/ui
npm install
npm run dev   # serves on http://localhost:3000
```

Now open `http://localhost:3000` in your host browser.

## 6. Working with Cursor on Ubuntu

### 6.1 Folder Structure Awareness

Cursor's AI features work best if your repo is *all inside one workspace*, with a clear `src/` and `apps/` layout. Keep:

```text
filecherry/
  src/
  apps/
  docs/
  tools/
```

Avoid huge nested Git submodules until later.

### 6.2 Remote Dev (WSL/VM)

If you're on Windows:

* Install Cursor on Windows.
* Attach to your Ubuntu environment using the WSL/remote extension pattern (same as VS Code).

Common gotcha: if Cursor isn't indexing your WSL project or the agent can't reach the network, you may need to adjust **HTTP compatibility mode** or run the built-in network diagnostics.

### 6.3 Debugging from Cursor

Useful patterns:

* Configure **launch configs** (Node + Python) so you can:

  * start the orchestrator with a debugger
  * start the UI with breakpoints.

* Add **npm and Python scripts** in `package.json` / `pyproject.toml`:

  * `npm run dev:orchestrator`
  * `npm run dev:ui`

* Use Cursor's terminal panes for:

  * `journalctl -u ollama -f`
  * ComfyUI logs
  * `tail -f dev-data/logs/orchestrator.log`.

### 6.4 Test Loops

* Add a `dev-data/inputs/` fixture set (few images + docs).
* Use Cursor prompts like:

  * "Run the orchestrator on the fixture inputs and show me the logs."
  * "Add logging around the pipeline selection."

## 7. Development Workflow Summary

1. Boot into Ubuntu / open WSL.
2. Start Ollama and ComfyUI.
3. Start orchestrator + UI with `FILECHERRY_DATA_DIR=dev-data/`.
4. Drop test files into `dev-data/inputs/`.
5. Open UI, describe what you want.
6. Iterate on orchestrator + pipelines using Cursor.

For deeper pipeline / USB imaging / deployment, see the other docs in this series.

