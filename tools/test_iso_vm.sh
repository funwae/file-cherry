#!/usr/bin/env bash
set -euo pipefail

# tools/test_iso_vm.sh
# Launch FileCherry ISO in a QEMU/KVM virtual machine for testing
#
# Usage: ./tools/test_iso_vm.sh
# Requires: qemu-system-x86_64 (install with: sudo apt install qemu-kvm qemu-system-x86_64)

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_FILE="${PROJECT_ROOT}/build/output/filecherry-0.1.0.iso"

if [[ ! -f "$ISO_FILE" ]]; then
  echo "Error: ISO not found at $ISO_FILE"
  echo "Build the ISO first with: sudo ./tools/build_iso.sh"
  exit 1
fi

# Check if qemu is installed (try different command names)
QEMU_CMD=""
for cmd in qemu-system-x86_64 qemu-system-x86; do
  if command -v "$cmd" &>/dev/null; then
    QEMU_CMD="$cmd"
    break
  fi
done

if [[ -z "$QEMU_CMD" ]]; then
  echo "Error: qemu-system-x86_64 or qemu-system-x86 is not installed"
  echo "Install it with: sudo apt install qemu-system-x86"
  echo "Or with GUI: sudo apt install qemu-system-gui"
  exit 1
fi

echo "Starting FileCherry ISO in QEMU VM..."
echo "ISO: $ISO_FILE"
echo ""

# Quick check: verify ISO has boot sectors
if ! isoinfo -d -i "$ISO_FILE" &>/dev/null; then
  echo "Warning: Could not read ISO metadata. ISO may be corrupted."
fi

echo "VM Configuration:"
echo "  - RAM: 4GB (adjust with -m option)"
echo "  - CPUs: 2 (adjust with -smp option)"
echo "  - Boot: From CD-ROM only (network disabled to prevent iPXE)"
echo ""
echo "Press Ctrl+Alt+G to release mouse/keyboard"
echo "Press Ctrl+Alt+F to toggle fullscreen"
echo "Press Ctrl+Alt+2 to open QEMU monitor (type 'quit' to exit)"
echo ""

# Launch QEMU with the ISO
# -m 4096: 4GB RAM (adjust if you have less)
# -smp 2: 2 CPU cores
# -enable-kvm: Use KVM acceleration (faster, requires hardware support)
# -cdrom: Boot from ISO
# -boot order=cd: Explicitly boot from CD-ROM first (no network = no iPXE)
# No network device specified = network boot disabled, prevents iPXE fallback
$QEMU_CMD \
  -m 4096 \
  -smp 2 \
  -enable-kvm \
  -cdrom "$ISO_FILE" \
  -boot order=cd \
  -vga std \
  -usb -device usb-tablet

echo ""
echo "VM shutdown complete."

