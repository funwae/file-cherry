# ISO Build Script – tools/build_iso.sh

This file describes and contains the `tools/build_iso.sh` script which automates building a **FileCherry** ISO from an Ubuntu base image.

> **Note:** This is a reference implementation. You may tune paths and packages as needed.

## 1. Script Location

- Path: `tools/build_iso.sh`
- Make executable:
```bash
chmod +x tools/build_iso.sh
```
Run with:
```bash
sudo tools/build_iso.sh
```
(`sudo` is required for mount, chroot, and ISO operations.)

## 2. Script Contents

```bash
#!/usr/bin/env bash
set -euo pipefail

# tools/build_iso.sh
# Build a FileCherry Ubuntu-based live ISO.
#
# WARNING: Run on a dedicated build host or VM. Requires sudo.

# ----- CONFIG -----
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
WORK_DIR="$BUILD_DIR/work"
OUTPUT_DIR="$BUILD_DIR/output"
UBUNTU_ISO_URL="${UBUNTU_ISO_URL:-https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso}"
BASE_ISO="$BUILD_DIR/ubuntu-base.iso"
VERSION_FILE="$PROJECT_ROOT/VERSION"
VERSION="$(cat "$VERSION_FILE" 2>/dev/null || echo "0.0.0")"
ISO_NAME="filecherry-${VERSION}.iso"
ISO_OUTPUT="$OUTPUT_DIR/$ISO_NAME"

# ----- FUNCTIONS -----
log() { echo "[build_iso] $*"; }

run_in_chroot() {
  chroot "$WORK_DIR/edit" /bin/bash -c "$*"
}

# ----- PREP -----
log "Creating build directories..."
mkdir -p "$BUILD_DIR" "$WORK_DIR" "$OUTPUT_DIR"

if [[ ! -f "$BASE_ISO" ]]; then
  log "Downloading base Ubuntu ISO..."
  curl -L "$UBUNTU_ISO_URL" -o "$BASE_ISO"
else
  log "Base ISO already present at $BASE_ISO"
fi

# ----- EXTRACT BASE ISO -----
log "Mounting base ISO..."
ISO_MOUNT="$WORK_DIR/iso_mount"
mkdir -p "$ISO_MOUNT"
mount -o loop "$BASE_ISO" "$ISO_MOUNT"

log "Copying ISO contents..."
mkdir -p "$WORK_DIR/iso_root"
rsync -a "$ISO_MOUNT/" "$WORK_DIR/iso_root"

log "Extracting squashfs filesystem..."
mkdir -p "$WORK_DIR/edit"
unsquashfs -d "$WORK_DIR/edit" "$ISO_MOUNT/casper/filesystem.squashfs"

umount "$ISO_MOUNT"

# ----- CUSTOMIZE CHROOT -----
log "Setting up chroot..."
# Bind mount special filesystems
mount --bind /dev "$WORK_DIR/edit/dev"
mount --bind /run "$WORK_DIR/edit/run"
mount --bind /sys "$WORK_DIR/edit/sys"
mount --bind /proc "$WORK_DIR/edit/proc"

log "Updating packages inside chroot..."
run_in_chroot "apt-get update && apt-get -y upgrade"

log "Installing core dependencies..."
run_in_chroot "DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip git curl wget nodejs npm \
  squashfs-tools xz-utils net-tools"

# ---- INSTALL OLLAMA ----
log "Installing Ollama..."
run_in_chroot "curl -fsSL https://ollama.com/install.sh | bash || true"

# ---- PULL DEFAULT MODEL ----
log "Setting up Ollama service and pulling phi3:mini model..."
# Start Ollama service and wait for it to be ready
run_in_chroot "systemctl enable ollama || true"
run_in_chroot "systemctl start ollama || true"
log "Waiting for Ollama service to be ready..."
run_in_chroot "sleep 10"
# Verify Ollama is responding
run_in_chroot "timeout 30 bash -c 'until curl -s http://127.0.0.1:11434/api/tags > /dev/null; do sleep 2; done' || true"
log "Pulling phi3:mini model (this may take several minutes)..."
run_in_chroot "ollama pull phi3:mini"
# Verify model was pulled successfully
log "Verifying phi3:mini model installation..."
run_in_chroot "ollama list | grep -q 'phi3:mini' && echo 'phi3:mini model installed successfully' || echo 'WARNING: phi3:mini model not found'"

# ---- COPY FILECHERRY CODE ----
log "Copying FileCherry repo into chroot..."
rm -rf "$WORK_DIR/edit/opt/filecherry"
mkdir -p "$WORK_DIR/edit/opt"
rsync -a --exclude build --exclude .git "$PROJECT_ROOT/" "$WORK_DIR/edit/opt/filecherry/"

# ---- PYTHON ENV ----
log "Creating Python venv..."
run_in_chroot "cd /opt/filecherry && python3 -m venv .venv && \
  . .venv/bin/activate && pip install -U pip && \
  if [ -f requirements.txt ]; then pip install -r requirements.txt; fi"

# ---- BUILD UI ----
log "Building UI..."
run_in_chroot "cd /opt/filecherry/apps/ui && npm install && npm run build"

# ---- SYSTEMD SERVICES ----
log "Installing systemd services..."
cp "$PROJECT_ROOT/docs/systemd/filecherry-orchestrator.service" "$WORK_DIR/edit/etc/systemd/system/"
cp "$PROJECT_ROOT/docs/systemd/filecherry-ui.service" "$WORK_DIR/edit/etc/systemd/system/"
# (ComfyUI and Ollama service units should also be copied here.)

run_in_chroot "systemctl enable filecherry-orchestrator.service || true"
run_in_chroot "systemctl enable filecherry-ui.service || true"

# ---- VERSION FILE ----
log "Writing version file..."
echo "$VERSION" > "$WORK_DIR/edit/etc/filecherry-version"

# ---- CLEANUP ----
log "Cleaning apt caches..."
run_in_chroot "apt-get clean"

# Unmount special filesystems
umount "$WORK_DIR/edit/dev" || true
umount "$WORK_DIR/edit/run" || true
umount "$WORK_DIR/edit/sys" || true
umount "$WORK_DIR/edit/proc" || true

# ----- REPACK SQUASHFS & ISO -----
log "Rebuilding squashfs..."
mksquashfs "$WORK_DIR/edit" "$WORK_DIR/filesystem.squashfs" -noappend

log "Updating ISO root with new squashfs..."
cp "$WORK_DIR/filesystem.squashfs" "$WORK_DIR/iso_root/casper/filesystem.squashfs"

log "Regenerating manifest..."
chroot "$WORK_DIR/edit" dpkg-query -W --showformat='${Package} ${Version}\n' > "$WORK_DIR/iso_root/casper/filesystem.manifest"

log "Creating new ISO at $ISO_OUTPUT..."
xorriso -as mkisofs \
  -r -V "FILECHERRY_${VERSION}" \
  -o "$ISO_OUTPUT" \
  -J -l -cache-inodes \
  -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
  -b isolinux/isolinux.bin \
     -c isolinux/boot.cat \
     -no-emul-boot -boot-load-size 4 -boot-info-table \
  -eltorito-alt-boot \
  -e boot/grub/efi.img \
  -no-emul-boot \
  "$WORK_DIR/iso_root"

log "Done. ISO created at: $ISO_OUTPUT"
```

## 3. Notes & Customization

* You may adjust which packages are installed in the `apt-get install` line.
* Systemd units are copied from `docs/systemd/` here; you can move them elsewhere.
* When you're comfortable, you can add **Ollama install** inside the chroot using its official script.

