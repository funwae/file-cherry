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
UBUNTU_ISO_URL="${UBUNTU_ISO_URL:-https://releases.ubuntu.com/24.04/ubuntu-24.04.3-desktop-amd64.iso}"
BASE_ISO="$BUILD_DIR/ubuntu-base.iso"
VERSION_FILE="$PROJECT_ROOT/VERSION"
VERSION="$(cat "$VERSION_FILE" 2>/dev/null || echo "0.0.0")"
ISO_NAME="filecherry-${VERSION}.iso"
ISO_OUTPUT="$OUTPUT_DIR/$ISO_NAME"

# ----- FUNCTIONS -----
log() { echo "[build_iso] $*"; }

run_in_chroot() {
  # Try /bin/bash first, fallback to /usr/bin/bash or /bin/sh
  if [[ -f "$WORK_DIR/edit/bin/bash" ]]; then
    chroot "$WORK_DIR/edit" /bin/bash -c "$*"
  elif [[ -f "$WORK_DIR/edit/usr/bin/bash" ]]; then
    chroot "$WORK_DIR/edit" /usr/bin/bash -c "$*"
  elif [[ -f "$WORK_DIR/edit/bin/sh" ]]; then
    chroot "$WORK_DIR/edit" /bin/sh -c "$*"
  else
    log "Error: No shell found in chroot. Extracted filesystem may be incomplete."
    log "Checking extracted filesystem..."
    sudo ls -la "$WORK_DIR/edit/bin" 2>/dev/null | head -10 || true
    sudo ls -la "$WORK_DIR/edit/usr/bin" 2>/dev/null | head -10 || true
    exit 1
  fi
}

cleanup() {
  log "Cleaning up mounts..."
  umount "$WORK_DIR/edit/dev" 2>/dev/null || true
  umount "$WORK_DIR/edit/run" 2>/dev/null || true
  umount "$WORK_DIR/edit/sys" 2>/dev/null || true
  umount "$WORK_DIR/edit/proc" 2>/dev/null || true
  umount "$WORK_DIR/iso_mount" 2>/dev/null || true
}

trap cleanup EXIT

# ----- PRE-FLIGHT CHECKS -----
log "Running pre-flight checks..."

# Check required tools
for cmd in unsquashfs mksquashfs xorriso rsync; do
  if ! command -v "$cmd" &>/dev/null; then
    log "Error: $cmd is not installed. Please install it first."
    log "Try: sudo apt install squashfs-tools xorriso rsync"
    exit 1
  fi
done

# Check for syslinux-utils (needed for hybrid ISO/USB boot with Etcher/Rufus)
if ! dpkg -l 2>/dev/null | grep -q "^ii.*syslinux-utils"; then
  log "Warning: syslinux-utils not installed. ISO will not be bootable from USB."
  log "Install with: sudo apt install syslinux-utils"
  log "This is REQUIRED for Etcher/Rufus compatibility."
fi

# Check disk space (need at least 30GB free for build)
AVAILABLE_SPACE=$(df "$BUILD_DIR" 2>/dev/null | tail -1 | awk '{print $4}')
if [[ -n "$AVAILABLE_SPACE" ]] && [[ "$AVAILABLE_SPACE" -lt 31457280 ]]; then
  log "Warning: Less than 30GB free space available. Build may fail."
  log "Available: $(df -h "$BUILD_DIR" | tail -1 | awk '{print $4}')"
fi

# Validate version format (ISO 9660 volume labels: uppercase, no special chars, max 32 chars)
VOLUME_LABEL=$(echo "FILECHERRY_${VERSION}" | tr '[:lower:]' '[:upper:]' | tr -cd 'A-Z0-9_' | cut -c1-32)
if [[ "$VOLUME_LABEL" != "FILECHERRY_${VERSION}" ]]; then
  log "Warning: Volume label adjusted for ISO 9660 compliance: $VOLUME_LABEL"
fi

log "Pre-flight checks passed"

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
sudo mount -o loop "$BASE_ISO" "$ISO_MOUNT" || {
  log "Error mounting ISO. Make sure you have sudo privileges."
  exit 1
}

log "Copying ISO contents (including boot files)..."
mkdir -p "$WORK_DIR/iso_root"
rsync -a "$ISO_MOUNT/" "$WORK_DIR/iso_root"

# Check for boot files in various locations (Ubuntu 24.04+ uses GRUB2 EFI)
log "Checking for boot files..."
BOOT_FILES_FOUND=false

# Check isolinux (legacy BIOS boot)
if [[ -f "$WORK_DIR/iso_root/isolinux/isolinux.bin" ]]; then
  log "Found isolinux boot: isolinux/isolinux.bin"
  BOOT_FILES_FOUND=true
fi

# Check GRUB EFI boot (modern Ubuntu)
if [[ -f "$WORK_DIR/iso_root/boot/grub/efi.img" ]]; then
  log "Found GRUB EFI boot: boot/grub/efi.img"
  BOOT_FILES_FOUND=true
fi

# Check EFI/boot (UEFI boot) - note: lowercase "boot" in Ubuntu 24.04
if [[ -f "$WORK_DIR/iso_root/EFI/boot/bootx64.efi" ]] || [[ -f "$WORK_DIR/iso_root/EFI/boot/grubx64.efi" ]]; then
  log "Found UEFI boot files in EFI/boot/"
  BOOT_FILES_FOUND=true
fi

# Check for BIOS boot via GRUB eltorito.img (Ubuntu 24.04 uses this instead of isolinux)
if [[ -f "$WORK_DIR/iso_root/boot/grub/i386-pc/eltorito.img" ]]; then
  log "Found GRUB BIOS boot: boot/grub/i386-pc/eltorito.img"
  BOOT_FILES_FOUND=true
fi

# Check boot/grub (GRUB2 configuration)
if [[ -d "$WORK_DIR/iso_root/boot/grub" ]] && [[ -f "$WORK_DIR/iso_root/boot/grub/grub.cfg" ]]; then
  log "Found GRUB2 configuration: boot/grub/grub.cfg"
  BOOT_FILES_FOUND=true
fi

if [[ "$BOOT_FILES_FOUND" != "true" ]]; then
  log "ERROR: No boot files found after copying ISO contents!"
  log "Searched for:"
  log "  - boot/grub/i386-pc/eltorito.img (GRUB BIOS)"
  log "  - isolinux/isolinux.bin (legacy)"
  log "  - EFI/boot/bootx64.efi (UEFI)"
  log "  - EFI/boot/grubx64.efi (UEFI)"
  log "  - boot/grub/grub.cfg (GRUB config)"
  log ""
  log "Listing boot-related directories in ISO root:"
  find "$WORK_DIR/iso_root" -type d \( -name "boot" -o -name "isolinux" -o -name "EFI" -o -name "grub" \) 2>/dev/null | head -10 || true
  log ""
  log "Listing boot-related files:"
  find "$WORK_DIR/iso_root" -type f \( -name "*.bin" -o -name "*.img" -o -name "*.efi" -o -name "grub.cfg" \) 2>/dev/null | head -20 || true
  exit 1
fi
log "✓ Boot files found and copied successfully"

log "Extracting squashfs filesystem..."
# Clean up any existing extraction directory from previous runs
sudo rm -rf "$WORK_DIR/edit"

# Find the squashfs file (Ubuntu 24.04+ uses modular structure)
SQUASHFS_FILE=""
# Try standard locations first (older Ubuntu versions)
if [[ -f "$ISO_MOUNT/casper/filesystem.squashfs" ]]; then
  SQUASHFS_FILE="$ISO_MOUNT/casper/filesystem.squashfs"
elif [[ -f "$ISO_MOUNT/casper/filesystem.squashfs.verity" ]]; then
  SQUASHFS_FILE="$ISO_MOUNT/casper/filesystem.squashfs.verity"
# Ubuntu 24.04.3+ uses modular squashfs - use the full base system (largest)
# The "minimal" variants are too minimal and may not include bash
elif [[ -f "$ISO_MOUNT/casper/minimal.squashfs" ]]; then
  SQUASHFS_FILE="$ISO_MOUNT/casper/minimal.squashfs"
  log "Using modular squashfs: minimal.squashfs (full base system - 1.7GB)"
# Fallback to live system if base not available
elif [[ -f "$ISO_MOUNT/casper/minimal.standard.live.squashfs" ]]; then
  SQUASHFS_FILE="$ISO_MOUNT/casper/minimal.standard.live.squashfs"
  log "Using modular squashfs: minimal.standard.live.squashfs (live desktop system)"
# Last resort: find largest squashfs file
else
  SQUASHFS_FILE=$(find "$ISO_MOUNT/casper" -name "*.squashfs" -type f -exec ls -S {} + 2>/dev/null | head -1)
  if [[ -n "$SQUASHFS_FILE" ]]; then
    log "Using largest squashfs found: $SQUASHFS_FILE"
  fi
fi

if [[ -z "$SQUASHFS_FILE" || ! -f "$SQUASHFS_FILE" ]]; then
  log "Error: Could not find squashfs filesystem in ISO"
  log "Available squashfs files in casper/:"
  find "$ISO_MOUNT/casper" -name "*.squashfs" -type f -exec ls -lh {} + 2>/dev/null | head -10 || true
  exit 1
fi

log "Found squashfs at: $SQUASHFS_FILE"
log "Extracting squashfs filesystem (this may take a few minutes)..."
sudo unsquashfs -d "$WORK_DIR/edit" "$SQUASHFS_FILE"

# Verify extraction succeeded and bash exists
log "Verifying extracted filesystem..."
if [[ ! -f "$WORK_DIR/edit/bin/bash" ]] && [[ ! -f "$WORK_DIR/edit/usr/bin/bash" ]]; then
  log "ERROR: Extracted filesystem does not contain bash!"
  log "This squashfs may be too minimal. Trying to find bash location..."
  sudo find "$WORK_DIR/edit" -name "bash" -type f 2>/dev/null | head -5 || true
  log "Available squashfs files in ISO:"
  find "$ISO_MOUNT/casper" -name "*.squashfs" -type f -exec ls -lh {} + 2>/dev/null || true
  log "Consider using a different squashfs file (e.g., minimal.squashfs instead of minimal.standard.live.squashfs)"
  exit 1
fi
log "Filesystem extraction verified - bash found"

sudo umount "$ISO_MOUNT"

# ----- CUSTOMIZE CHROOT -----
log "Setting up chroot..."
# Create mount points if they don't exist
sudo mkdir -p "$WORK_DIR/edit/dev" "$WORK_DIR/edit/run" "$WORK_DIR/edit/sys" "$WORK_DIR/edit/proc"
# Bind mount special filesystems
sudo mount --bind /dev "$WORK_DIR/edit/dev"
sudo mount --bind /run "$WORK_DIR/edit/run"
sudo mount --bind /sys "$WORK_DIR/edit/sys"
sudo mount --bind /proc "$WORK_DIR/edit/proc"

log "Updating packages inside chroot..."
run_in_chroot "apt-get update && apt-get -y upgrade"

log "Installing core dependencies..."
run_in_chroot "DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip git curl wget nodejs npm \
  squashfs-tools xz-utils net-tools chromium-browser \
  exfatprogs dosfstools"

# ---- CREATE FILECHERRY USER ----
log "Creating filecherry user..."
run_in_chroot "useradd -m -s /bin/bash filecherry || true"
run_in_chroot "usermod -aG sudo filecherry || true"

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

# ---- INSTALL COMFYUI ----
log "Installing ComfyUI..."
run_in_chroot "mkdir -p /opt && cd /opt && \
  git clone https://github.com/comfyanonymous/ComfyUI.git || true && \
  cd ComfyUI && python3 -m venv venv && \
  . venv/bin/activate && pip install -r requirements.txt || true"

# ---- COPY FILECHERRY CODE ----
log "Copying FileCherry repo into chroot..."
sudo rm -rf "$WORK_DIR/edit/opt/filecherry"
sudo mkdir -p "$WORK_DIR/edit/opt"
sudo rsync -a --exclude build --exclude .git --exclude node_modules \
  --exclude .venv --exclude __pycache__ \
  "$PROJECT_ROOT/" "$WORK_DIR/edit/opt/filecherry/"

# Set ownership (do this inside chroot where the user exists)
log "Setting file ownership..."
run_in_chroot "chown -R filecherry:filecherry /opt/filecherry || true"

# ---- PYTHON ENV ----
log "Creating Python venv..."
run_in_chroot "cd /opt/filecherry && python3 -m venv .venv && \
  . .venv/bin/activate && pip install -U pip && \
  if [ -f requirements.txt ]; then pip install -r requirements.txt; fi"

# ---- BUILD UI ----
log "Building UI..."
run_in_chroot "cd /opt/filecherry/apps/ui && \
  npm install && npm run build"
# Verify server.js exists
if [[ ! -f "$WORK_DIR/edit/opt/filecherry/apps/ui/server.js" ]]; then
  log "ERROR: server.js not found after UI build!"
  exit 1
fi
log "✓ UI built successfully"

# ---- SYSTEMD SERVICES ----
log "Installing systemd services..."
sudo cp "$PROJECT_ROOT/docs/systemd/filecherry-orchestrator.service" \
  "$WORK_DIR/edit/etc/systemd/system/"
sudo cp "$PROJECT_ROOT/docs/systemd/filecherry-ui.service" \
  "$WORK_DIR/edit/etc/systemd/system/"
sudo cp "$PROJECT_ROOT/docs/systemd/comfyui.service" \
  "$WORK_DIR/edit/etc/systemd/system/"
sudo cp "$PROJECT_ROOT/docs/systemd/data.mount" \
  "$WORK_DIR/edit/etc/systemd/system/"
sudo cp "$PROJECT_ROOT/docs/systemd/filecherry-setup.service" \
  "$WORK_DIR/edit/etc/systemd/system/"
sudo cp "$PROJECT_ROOT/docs/systemd/filecherry-kiosk.service" \
  "$WORK_DIR/edit/etc/systemd/system/" || log "Warning: kiosk service not found, skipping"
sudo cp "$PROJECT_ROOT/docs/systemd/logrotate.service" \
  "$WORK_DIR/edit/etc/systemd/system/"
sudo cp "$PROJECT_ROOT/docs/systemd/logrotate.timer" \
  "$WORK_DIR/edit/etc/systemd/system/"

run_in_chroot "systemctl enable filecherry-orchestrator.service || true"
run_in_chroot "systemctl enable filecherry-ui.service || true"
run_in_chroot "systemctl enable comfyui.service || true"
run_in_chroot "systemctl enable data.mount || true"
run_in_chroot "systemctl enable filecherry-setup.service || true"
if [[ -f "$WORK_DIR/edit/etc/systemd/system/filecherry-kiosk.service" ]]; then
  run_in_chroot "systemctl enable filecherry-kiosk.service || true"
fi
run_in_chroot "systemctl enable logrotate.timer || true"

# ---- COPY TOOLS ----
log "Installing utility scripts..."
sudo cp "$PROJECT_ROOT/tools/network-doctor.sh" \
  "$WORK_DIR/edit/opt/filecherry/tools/"
sudo cp "$PROJECT_ROOT/tools/rotate_logs.sh" \
  "$WORK_DIR/edit/opt/filecherry/tools/"
sudo cp "$PROJECT_ROOT/tools/filecherry-jobs" \
  "$WORK_DIR/edit/opt/filecherry/tools/"
sudo cp "$PROJECT_ROOT/tools/filecherry-job" \
  "$WORK_DIR/edit/opt/filecherry/tools/"
sudo cp "$PROJECT_ROOT/tools/filecherry-logs" \
  "$WORK_DIR/edit/opt/filecherry/tools/"
sudo chmod +x "$WORK_DIR/edit/opt/filecherry/tools/"*.sh
sudo chmod +x "$WORK_DIR/edit/opt/filecherry/tools/filecherry-"*

# Create symlinks in /usr/local/bin
run_in_chroot "ln -sf /opt/filecherry/tools/filecherry-jobs /usr/local/bin/filecherry-jobs || true"
run_in_chroot "ln -sf /opt/filecherry/tools/filecherry-job /usr/local/bin/filecherry-job || true"
run_in_chroot "ln -sf /opt/filecherry/tools/filecherry-logs /usr/local/bin/filecherry-logs || true"

# ---- VERSION FILE ----
log "Writing version file..."
echo "$VERSION" | sudo tee "$WORK_DIR/edit/etc/filecherry-version" > /dev/null

# ---- CLEANUP ----
log "Cleaning apt caches..."
run_in_chroot "apt-get clean"

# Unmount special filesystems (but keep ISO mount for boot file checks)
log "Unmounting chroot filesystems (keeping ISO mount for boot files)..."
umount "$WORK_DIR/edit/dev" 2>/dev/null || true
umount "$WORK_DIR/edit/run" 2>/dev/null || true
umount "$WORK_DIR/edit/sys" 2>/dev/null || true
umount "$WORK_DIR/edit/proc" 2>/dev/null || true
# Don't unmount iso_mount yet - we need it for boot file verification

# ----- REPACK SQUASHFS & ISO -----
log "Rebuilding squashfs..."
sudo mksquashfs "$WORK_DIR/edit" "$WORK_DIR/filesystem.squashfs" -noappend -comp xz

log "Updating ISO root with new squashfs..."
sudo cp "$WORK_DIR/filesystem.squashfs" "$WORK_DIR/iso_root/casper/filesystem.squashfs"

log "Regenerating manifest..."
# Check if chroot is still accessible (might be unmounted)
if [[ -f "$WORK_DIR/edit/bin/bash" ]] || [[ -f "$WORK_DIR/edit/usr/bin/bash" ]]; then
  sudo chroot "$WORK_DIR/edit" dpkg-query -W --showformat='${Package} ${Version}\n' > "$WORK_DIR/iso_root/casper/filesystem.manifest" 2>/dev/null || {
    log "Warning: Could not regenerate manifest. Using placeholder."
    echo "# FileCherry ${VERSION} - Manifest generation skipped" > "$WORK_DIR/iso_root/casper/filesystem.manifest"
  }
else
  log "Warning: Chroot not accessible for manifest generation. Using placeholder."
  echo "# FileCherry ${VERSION} - Manifest generation skipped" > "$WORK_DIR/iso_root/casper/filesystem.manifest"
fi

# Check what boot files exist in ISO root and copy from original ISO if missing
log "Checking boot structure..."
# Remount ISO if needed
if [[ ! -d "$WORK_DIR/iso_mount" ]] || ! mountpoint -q "$WORK_DIR/iso_mount" 2>/dev/null; then
  log "Remounting ISO to check boot structure..."
  sudo mount -o loop "$BASE_ISO" "$WORK_DIR/iso_mount" 2>/dev/null || true
fi

# Copy isolinux files if missing
if [[ ! -f "$WORK_DIR/iso_root/isolinux/isolinux.bin" ]]; then
  if [[ -d "$WORK_DIR/iso_mount" ]] && mountpoint -q "$WORK_DIR/iso_mount" 2>/dev/null && [[ -f "$WORK_DIR/iso_mount/isolinux/isolinux.bin" ]]; then
    log "Copying isolinux boot files from original ISO..."
    sudo mkdir -p "$WORK_DIR/iso_root/isolinux"
    sudo cp -r "$WORK_DIR/iso_mount/isolinux/"* "$WORK_DIR/iso_root/isolinux/" 2>/dev/null || true
  else
    log "Warning: isolinux boot files not found in ISO root or original ISO"
  fi
else
  log "Found isolinux boot files in ISO root"
fi

# Copy EFI boot files if missing
if [[ ! -f "$WORK_DIR/iso_root/boot/grub/efi.img" ]]; then
  if [[ -d "$WORK_DIR/iso_mount" ]] && mountpoint -q "$WORK_DIR/iso_mount" 2>/dev/null && [[ -f "$WORK_DIR/iso_mount/boot/grub/efi.img" ]]; then
    log "Copying EFI boot files from original ISO..."
    sudo mkdir -p "$WORK_DIR/iso_root/boot/grub"
    sudo cp "$WORK_DIR/iso_mount/boot/grub/efi.img" "$WORK_DIR/iso_root/boot/grub/efi.img" 2>/dev/null || true
  else
    log "Warning: EFI boot files not found in ISO root or original ISO"
  fi
else
  log "Found EFI boot files in ISO root"
fi

# Find isohdpfx.bin on host system (for hybrid MBR)
# On Ubuntu, syslinux-utils doesn't include isohdpfx.bin, so we'll use isohybrid command instead
ISOHDPFX_BIN=""
for path in /usr/lib/ISOLINUX/isohdpfx.bin /usr/lib/syslinux/isohdpfx.bin /usr/share/syslinux/isohdpfx.bin; do
  if [[ -f "$path" ]]; then
    ISOHDPFX_BIN="$path"
    log "Found isohdpfx.bin at: $path"
    break
  fi
done

# Check if isohybrid command is available (alternative method)
HAS_ISOHYBRID=false
if command -v isohybrid &>/dev/null; then
  HAS_ISOHYBRID=true
  log "Found isohybrid command (will use for hybrid boot)"
fi

log "Creating new ISO at $ISO_OUTPUT..."
cd "$WORK_DIR/iso_root"

# Build xorriso command - start with basic options
# Use -iso-level 4 to support files larger than 4GB (required for large squashfs)
XORRISO_ARGS=(
  -as mkisofs
  -r
  -iso-level 4
  -V "$VOLUME_LABEL"
  -o "$ISO_OUTPUT"
  -J
  -l
)

# Add hybrid MBR/GPT support (makes ISO bootable from USB with Etcher/Rufus)
# This is REQUIRED for USB booting - without it, the ISO is only bootable from CD
if [[ -n "$ISOHDPFX_BIN" ]]; then
  XORRISO_ARGS+=(-isohybrid-mbr "$ISOHDPFX_BIN")
  # Also add GPT support for better UEFI compatibility
  XORRISO_ARGS+=(-isohybrid-gpt-basdat)
  log "✓ Configuring hybrid ISO (bootable from USB with Etcher/Rufus)"
else
  # Try using xorriso's built-in part_like_isohybrid option
  # This makes the ISO appear as a disk with a partition table
  XORRISO_ARGS+=(-part_like_isohybrid)
  log "✓ Using xorriso's built-in hybrid support (part_like_isohybrid)"
  log "Note: Will also try isohybrid command after ISO creation for better compatibility"
fi

# Configure boot sectors
BOOT_CONFIGURED=false

# Ubuntu 24.04 uses GRUB for both BIOS and UEFI boot
# BIOS boot: boot/grub/i386-pc/eltorito.img
# UEFI boot: EFI/boot/bootx64.efi or EFI/boot/grubx64.efi

# Add GRUB BIOS boot (legacy BIOS) if available
if [[ -f "$WORK_DIR/iso_root/boot/grub/i386-pc/eltorito.img" ]]; then
  log "Configuring GRUB BIOS boot (legacy BIOS)..."
  XORRISO_ARGS+=(
    -b boot/grub/i386-pc/eltorito.img
    -no-emul-boot
    -boot-load-size 4
    -boot-info-table
  )
  BOOT_CONFIGURED=true
fi

# Add isolinux boot (legacy, if present) - Ubuntu 24.04 doesn't use this but check anyway
if [[ -f "$WORK_DIR/iso_root/isolinux/isolinux.bin" ]]; then
  log "Configuring isolinux boot (legacy BIOS fallback)..."
  XORRISO_ARGS+=(
    -b isolinux/isolinux.bin
    -c isolinux/boot.cat
    -no-emul-boot
    -boot-load-size 4
    -boot-info-table
  )
  BOOT_CONFIGURED=true
fi

# Add UEFI boot (EFI/boot - note lowercase) if available
if [[ -f "$WORK_DIR/iso_root/EFI/boot/bootx64.efi" ]] || [[ -f "$WORK_DIR/iso_root/EFI/boot/grubx64.efi" ]]; then
  log "Configuring UEFI boot (EFI/boot)..."
  # Use bootx64.efi as primary, grubx64.efi as fallback
  EFI_BOOT_FILE=""
  if [[ -f "$WORK_DIR/iso_root/EFI/boot/bootx64.efi" ]]; then
    EFI_BOOT_FILE="EFI/boot/bootx64.efi"
  elif [[ -f "$WORK_DIR/iso_root/EFI/boot/grubx64.efi" ]]; then
    EFI_BOOT_FILE="EFI/boot/grubx64.efi"
  fi

  if [[ -n "$EFI_BOOT_FILE" ]]; then
    XORRISO_ARGS+=(
      -eltorito-alt-boot
      -e "$EFI_BOOT_FILE"
      -no-emul-boot
    )
    BOOT_CONFIGURED=true
  fi
fi

# Fail if no boot configuration was added
if [[ "$BOOT_CONFIGURED" != "true" ]]; then
  log "ERROR: No boot configuration added! ISO will not be bootable."
  log "Checked for:"
  log "  - $WORK_DIR/iso_root/boot/grub/i386-pc/eltorito.img"
  log "  - $WORK_DIR/iso_root/isolinux/isolinux.bin"
  log "  - $WORK_DIR/iso_root/EFI/boot/bootx64.efi"
  log "  - $WORK_DIR/iso_root/EFI/boot/grubx64.efi"
  exit 1
fi

# Add source directory
XORRISO_ARGS+=("$WORK_DIR/iso_root")

# Now we can unmount the ISO
log "Unmounting base ISO..."
umount "$WORK_DIR/iso_mount" 2>/dev/null || true

# Run xorriso
log "Running xorriso with ${#XORRISO_ARGS[@]} arguments..."
if sudo xorriso "${XORRISO_ARGS[@]}"; then
  # Verify ISO was created successfully
  if [[ -f "$ISO_OUTPUT" ]]; then
    ISO_SIZE=$(du -h "$ISO_OUTPUT" | cut -f1)
    log "✓ Success! ISO created at: $ISO_OUTPUT"
    log "✓ ISO size: $ISO_SIZE"

    # Verify boot sectors were written
    log "Verifying boot configuration..."
    if xorriso -indev "$ISO_OUTPUT" -report_el_torito as_mkisofs 2>&1 | grep -q "El Torito"; then
      log "✓ Boot sectors verified"
    else
      log "WARNING: Boot sectors may not be present. ISO might not be bootable."
    fi

    # Make ISO hybrid bootable for USB (if isohybrid is available and isohdpfx.bin wasn't found)
    if [[ -z "$ISOHDPFX_BIN" ]] && [[ "$HAS_ISOHYBRID" == "true" ]]; then
      log "Making ISO hybrid bootable with isohybrid command..."
      # Use -u flag for UEFI support, which is required for modern systems
      if sudo isohybrid -u "$ISO_OUTPUT" 2>&1; then
        log "✓ ISO made hybrid bootable (USB compatible)"
      else
        log "ERROR: isohybrid failed. Checking error..."
        # Try without -u flag as fallback
        log "Trying isohybrid without UEFI flag..."
        if sudo isohybrid "$ISO_OUTPUT" 2>&1; then
          log "✓ ISO made hybrid bootable (BIOS only, no UEFI)"
        else
          log "ERROR: isohybrid failed completely. ISO may not be bootable from USB."
          log "You may need to use Etcher's 'Flash and verify' or Rufus instead."
        fi
      fi
    fi

    # Verify it's not empty or corrupted
    if [[ $(stat -f%z "$ISO_OUTPUT" 2>/dev/null || stat -c%s "$ISO_OUTPUT" 2>/dev/null) -lt 1000000 ]]; then
      log "ERROR: ISO file is suspiciously small (< 1MB). Build may have failed."
      exit 1
    fi
  else
    log "ERROR: ISO file was not created at expected location: $ISO_OUTPUT"
    exit 1
  fi
else
  log "ERROR: xorriso failed. Check error messages above."
  exit 1
fi

