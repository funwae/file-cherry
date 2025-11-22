# FileCherry Deployment Guide

This guide covers:

- building the FileCherry OS image on Ubuntu
- creating a bootable USB with a **data partition** users can access on Mac/Windows
- basic post-boot checks.

## 1. Build Strategy Overview

We follow the classic Ubuntu **LiveCD customization** approach:

1. Start from an official Ubuntu ISO.
2. Extract and chroot into the filesystem.
3. Install our packages (Ollama, ComfyUI, orchestrator, UI).
4. Repack as a LiveISO.
5. Flash to USB and add a separate **data partition** for `/data`.

Later, we can automate this with scripts or tools like **Cubic**, but initial versions can be scripted manually.

## 2. Build Host Requirements

- Ubuntu 22.04/24.04 (VM or bare-metal).
- 50GB free disk.
- `squashfs-tools`, `xorriso`, `isolinux`, etc.

Install tools:

```bash
sudo apt update
sudo apt install -y squashfs-tools genisoimage xorriso isolinux \
  debootstrap syslinux-utils
```

## 3. High-Level Build Steps

### 3.1 Get Base ISO

```bash
mkdir -p ~/filecherry-build
cd ~/filecherry-build
wget https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso
```

### 3.2 Extract and Prepare Chroot

Follow the pattern in Ubuntu's LiveCD customization docs:

1. Mount ISO.
2. Copy filesystem.squashfs.
3. Unsquash, chroot, customize.

Pseudo-steps:

```bash
mkdir mnt iso_root edit
sudo mount -o loop ubuntu-24.04-desktop-amd64.iso mnt
rsync -a mnt/ iso_root
sudo unsquashfs mnt/casper/filesystem.squashfs
sudo mv squashfs-root edit
sudo chroot edit
```

Inside `chroot`:

* `apt update && apt upgrade`
* install Ollama, ComfyUI, Node, Python, etc.
* copy FileCherry orchestrator + UI code into `/opt/filecherry`.
* create systemd units (see below).

When done, clean apt caches, exit chroot.

## 4. Systemd Services

Create unit files inside `edit/etc/systemd/system/`:

### 4.1 `filecherry-orchestrator.service`

```ini
[Unit]
Description=FileCherry Orchestrator
After=network.target ollama.service comfyui.service

[Service]
Environment=FILECHERRY_DATA_DIR=/data
WorkingDirectory=/opt/filecherry
ExecStart=/opt/filecherry/.venv/bin/python -m src.orchestrator.main
Restart=on-failure
User=filecherry

[Install]
WantedBy=multi-user.target
```

### 4.2 `filecherry-ui.service`

```ini
[Unit]
Description=FileCherry Web UI
After=network.target

[Service]
WorkingDirectory=/opt/filecherry/apps/ui
ExecStart=/usr/bin/node server.js   # or `npm start` equivalent
Restart=on-failure
User=filecherry

[Install]
WantedBy=multi-user.target
```

### 4.3 ComfyUI & Ollama Services

Use the patterns from ComfyUI deployment guides to run it as a system service.

Example:

```ini
[Unit]
Description=ComfyUI System Service
After=network.target

[Service]
WorkingDirectory=/opt/ComfyUI
ExecStart=/opt/ComfyUI/venv/bin/python main.py --listen 0.0.0.0 --port 8188
Restart=always
User=filecherry

[Install]
WantedBy=multi-user.target
```

Ollama usually ships its own service unit; we just ensure it's enabled.

### 4.4 Enable Services

From inside chroot:

```bash
systemctl enable filecherry-orchestrator
systemctl enable filecherry-ui
systemctl enable comfyui
systemctl enable ollama
```

## 5. Repack ISO

Back on the build host (outside chroot), follow the LiveISO repack pattern:

1. Regenerate `filesystem.manifest`.
2. Re-squash `edit/` into `filesystem.squashfs`.
3. Rebuild ISO with `xorriso` or `genisoimage`.

(Exact commands omitted for brevity; we can codify them in `tools/build_iso.sh` based on the LiveCD docs.)

## 6. Create Bootable USB + Data Partition

Use `lsblk` to find your USB (e.g., `/dev/sdX`).

### 6.1 Flash ISO

Use `dd` or `balenaEtcher`:

```bash
sudo dd if=filecherry.iso of=/dev/sdX bs=4M status=progress && sync
```

(This writes the ISO, including the Ubuntu live system and EFI partition.)

### 6.2 Add Data Partition

After flashing:

1. Use `gparted` or `fdisk` on `/dev/sdX`.
2. Shrink the last partition (if needed) to free space.
3. Create a new partition in remaining space:
   * Type: exFAT (for Mac/Windows access) or ext4 (if Linux-only).
   * Label: `FILECHERRY_DATA`.

Format:

```bash
sudo mkfs.exfat -n FILECHERRY_DATA /dev/sdX3   # example
```

### 6.3 Mount as `/data` on Boot

Add a udev rule or systemd mount unit in the OS:

`/etc/systemd/system/data.mount`:

```ini
[Unit]
Description=FileCherry Data Partition

[Mount]
What=/dev/disk/by-label/FILECHERRY_DATA
Where=/data
Type=exfat
Options=uid=filecherry,gid=filecherry

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
systemctl enable data.mount
```

## 7. First Boot Checklist

On first boot from USB:

1. Hit `Esc/F12` to choose USB device.
2. Let Ubuntu live system boot into FileCherry session.
3. After login (or autologin), verify:

```bash
ls /data      # inputs/ outputs/ etc
systemctl status filecherry-orchestrator
systemctl status filecherry-ui
systemctl status comfyui
systemctl status ollama
curl http://localhost:3000/healthz
```

If all good, you're ready to hand it to users.

## 8. Mass Production (Later)

Once stable:

* Script the whole build pipeline in `tools/build.sh`.
* Use a USB duplication tool (or scripts with `dd`) to create multiple sticks.
* Keep a **version label** on the stick and in `/data/config/appliance.yaml`.

