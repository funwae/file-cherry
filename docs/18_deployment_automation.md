# Deployment Automation for FileCherry

This doc describes how to **automate** the ISO build and basic USB preparation so you can regenerate FileCherry appliances repeatably.

## 1. Build Inputs

- Base Ubuntu ISO (24.04)
- FileCherry repo (with orchestrator + UI + configs)
- Script: `tools/build_iso.sh` (see [ISO Build Script](19_iso_build_script.md))

## 2. Build Pipeline Overview

`build_iso.sh` automates:

1. Downloading the base ISO if missing.
2. Extracting its filesystem.
3. Chrooting + customizing:
   - install dependencies
   - copy FileCherry code
   - register systemd services.
4. Repacking `filesystem.squashfs`.
5. Creating a new ISO (`filecherry-<version>.iso`).

Later, we can extend this to:

- automatically partition a USB
- add a data partition
- pre-seed default `config/`.

## 3. Versioning & Metadata

We keep a simple metadata file `VERSION` at the repo root:

```text
0.1.0
```

`build_iso.sh` reads it and names output ISO:

```text
build/output/filecherry-0.1.0.iso
```

It also writes a small `/etc/filecherry-version` file inside the chroot so that the running appliance knows its version.

## 4. Build Environment

We recommend a dedicated **build host**:

* Ubuntu 22.04/24.04.
* 50GB free space.
* No need for GPU.

Install global build dependencies once:

```bash
sudo apt update
sudo apt install -y squashfs-tools genisoimage xorriso debootstrap \
  isolinux syslinux-utils curl wget rsync
```

## 5. Automated Steps Inside `build_iso.sh`

High-level pseudocode (the real script is in [ISO Build Script](19_iso_build_script.md)):

1. `BASE_ISO` download / verify.
2. Mount base ISO → copy contents to `work/iso_root`.
3. Extract `filesystem.squashfs` to `work/edit/`.
4. Chroot into `work/edit/`:
   * `apt` installs.
   * `curl` install script for Ollama.
   * clone & set up ComfyUI.
   * copy FileCherry repo to `/opt/filecherry`.
   * `pip install -r /opt/filecherry/requirements.txt`.
   * `npm install && npm run build` for UI.
   * set up systemd units.
5. Clean caches.
6. Rebuild `filesystem.squashfs`.
7. Rebuild ISO (keeping bootloaders / EFI bits from original ISO).

This follows the standard pattern used when customizing Ubuntu live images, merely automated into one script.

## 6. Post-Build Steps

Once `build_iso.sh` finishes:

1. Verify ISO:
   ```bash
   ls build/output/filecherry-*.iso
   file build/output/filecherry-0.1.0.iso
   ```
2. Test in a VM before giving to users:
   ```bash
   qemu-system-x86_64 -m 8192 -cdrom build/output/filecherry-0.1.0.iso
   ```
3. Flash to USB as per [Deployment Guide](15_deployment_guide.md).

## 7. Future Automation: USB Prep

Later we can add another script, `tools/prepare_usb.sh`, which will:

1. Take a device (e.g. `/dev/sdX`).
2. `dd` the ISO.
3. Create / format the data partition.
4. Populate default `/data/config/` structure.

For now, we call that out explicitly in [Deployment Guide](15_deployment_guide.md).

## 8. CI Integration (Future)

Hook `build_iso.sh` into a build pipeline (GitHub Actions / self-hosted runner):

* On tagged releases:
  * run tests
  * run `build_iso.sh` on a beefy self-hosted runner
  * upload ISO as release artifact.

The ISO build itself is usually too heavy for default cloud runners, but a self-hosted machine can handle it.

