# OS Image and Boot Specification

## Partitions

Recommend a 3-partition layout on the USB:

1. **EFI Partition** (`/dev/sdX1`)
   - Type: FAT32
   - Size: ~256–512MB
   - Contents: GRUB + bootloaders.

2. **System Partition** (`/dev/sdX2`)
   - Type: ext4
   - Size: 8–16GB (depending on models included)
   - Contents:
     - Minimal Ubuntu root filesystem.
     - Ollama, ComfyUI, Python environment.
   - Mounted as `/` (root).

3. **Data Partition** (`/dev/sdX3`)
   - Type: exFAT (for good cross-platform host support) or ext4 (if we require Linux for host).
   - Size: rest of drive.
   - Contents: user-facing folders.
   - Mounted as `/data`.

On Mac/Windows, only the **data partition** needs to be visible.

## Boot Process

1. UEFI firmware loads GRUB from EFI partition.
2. GRUB boots kernel + initrd from System partition.
3. Early init:
   - mount `/dev/sdX3` to `/data`.
   - ensure the presence of:
     - `/data/inputs`
     - `/data/outputs`
     - `/data/config`
     - `/data/logs`
   - create them if missing.

4. Systemd targets:
   - `multi-user.target` as base.
  - `filecherry-setup.service`:
    - validates folder structure
    - copies default configs if missing.
   - `ollama.service`:
     - starts Ollama server.
     - phi3:mini model is pre-installed in the ISO (pulled during build).
   - `comfyui.service`:
     - starts ComfyUI server.
   - `filecherry-orchestrator.service`:
     - starts orchestrator.
   - `filecherry-ui.service`:
     - starts web UI.
   - `kiosk-browser.service` (optional):
     - launches Chromium in kiosk mode pointing at `http://localhost:3000`.

## Live vs Installed

- **Mode 1 – Live-only (simpler start)**:
  - OS partition treated as read-only.
  - Updates applied by reflashing USB.

- **Mode 2 – Installable (later)**:
  - ability to install to local disk, leaving data partition in place.

## Updates

Initial strategy:

- New OS images distributed as ISO/IMG.
- Document simple update procedure:
  1. Backup `data` partition.
  2. Reflash `system` + `EFI` partitions.
  3. Restore `data` partition (or reuse if left untouched).

Later strategy:

- OTA-style updates via:
  - `filecherry-update` command pulling signed squashfs images.

## Hardware Requirements

Baseline target:

- CPU: 4-core x86_64
- RAM: 16GB recommended
- Disk: 128GB USB 3.0 or SSD
- GPU (for local image work):
  - NVIDIA GPU with at least 8–12GB VRAM
  - Proper drivers and CUDA libraries included.

