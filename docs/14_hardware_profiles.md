# FileCherry Hardware Profiles

## 1. Overview

FileCherry is flexible: it can run as a tiny "planning-only" appliance or as a full GPU-powered image/LLM workstation.

This doc defines recommended **profiles** so we can test against realistic hardware envelopes.

## 2. Profile A – Thin Client (Docs + Remote LLM)

**Use cases**

- Text-heavy workflows.
- Using remote/cloud LLMs or other servers for heavy lifting.
- Minimal image work.

**Suggested hardware**

- CPU: 2–4 core x86_64 (Intel NUC, small mini-PC).
- RAM: 8–16GB.
- Storage: 64–128GB SSD/USB.
- GPU: none required.
- Network: reliable Ethernet or Wi-Fi.

**Notes**

- ComfyUI is optional here; we may rely on cloud image services.
- Great candidate for **Level 1 subscription tier** built around remote APIs.

## 3. Profile B – Local GPU Appliance (Image + Docs, No Cloud)

**Use cases**

- On-prem Stable Diffusion and ComfyUI pipelines for image-heavy workflows (e.g. car dealerships, product photography).
- Mixed doc + image analysis.

**Suggested hardware**

- CPU: 6–8 core (e.g. Ryzen 5/7 or Intel i5/i7).
- RAM: 32GB.
- Storage: 1TB SSD (fast NVMe if possible).
- GPU:
  - NVIDIA RTX 3060 / 4060 or better.
  - **VRAM**: 12GB recommended for comfortable SDXL + larger pipelines.
- PSU: 650W+ good quality.

**Notes**

- FileCherry OS will include NVIDIA drivers and CUDA for this profile.
- We validate ComfyUI pipelines specifically on this VRAM baseline.

## 4. Profile C – Heavy GPU Rig

**Use cases**

- Multiple pipelines in parallel.
- Larger models (e.g. higher-res SDXL, future local LLMs).
- Multi-user scenarios via network.

**Suggested hardware**

- CPU: 8–16 core workstation class.
- RAM: 64–128GB.
- Storage: 2–4TB NVMe.
- GPU:
  - 24GB+ VRAM card (e.g. RTX 4090, 3090).
- Cooling & power sized appropriately.

**Notes**

- We may support **multi-GPU** for image batching.
- Only needed for power users; not required for v1 of FileCherry.

## 5. Profile D – Ultra-Low-Cost "Planner Stick"

**Use cases**

- Primarily document summarization and light LLM tasks.
- Minimal or no SD/ComfyUI; maybe only lightweight image operations.

**Suggested hardware**

- Single-board computer (e.g. ARM SBC or Raspberry Pi with enough RAM).
- RAM: 4–8GB.
- Storage: 64GB SSD or good-quality SD card + USB.
- No dedicated GPU.

**Notes**

- Might use CPU-only Ollama models (tiny, quantized).
- Performance will be slower; clearly document expectations.

## 6. Networking Considerations per Profile

### Thin Client / Cloud-heavy

- Must have stable outbound internet.
- Minimal inbound connectivity needs.

### Local GPU Appliance

- Should work fully **offline**.
- Networking optional (for updates / GitHub / monitoring).

### Heavy GPU Rig

- More likely to be multi-user across LAN.
- Consider running Ollama and ComfyUI exposed on LAN (see [Networking Guide](16_howtogetworking.md)).

## 7. Storage Layout & Wear

For USB-based boot:

- Prefer **USB SSD** over flash thumb drives for heavy write workloads.
- Data partition should sit on SSD or high-endurance flash.

For large models:

- Put model weights on fast internal SSD if possible; avoid storing multi-GB models on the same slow USB that hosts OS.

## 8. Test Matrix

For FileCherry's own QA:

- Ensure at least one machine for each profile A–C.
- Run e2e tests and record:
  - job time
  - resource usage
  - any VRAM/OOM errors.

