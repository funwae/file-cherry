#!/usr/bin/env bash
set -euo pipefail

# tools/prepare_usb.sh
# Prepare a USB drive with FileCherry ISO and data partition.
#
# Usage: sudo tools/prepare_usb.sh <iso_file> <device>
# Example: sudo tools/prepare_usb.sh build/output/filecherry-0.1.0.iso /dev/sdX
#
# WARNING: This will erase the target device. Double-check the device path!

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <iso_file> <device>"
  echo "Example: $0 build/output/filecherry-0.1.0.iso /dev/sdX"
  exit 1
fi

ISO_FILE="$1"
DEVICE="$2"

if [[ ! -f "$ISO_FILE" ]]; then
  echo "Error: ISO file not found: $ISO_FILE"
  exit 1
fi

if [[ ! -b "$DEVICE" ]]; then
  echo "Error: Device not found: $DEVICE"
  exit 1
fi

echo "WARNING: This will erase all data on $DEVICE"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Unmount any mounted partitions
echo "Unmounting existing partitions..."
sudo umount "${DEVICE}"* 2>/dev/null || true

# Flash ISO to device
echo "Flashing ISO to $DEVICE..."
sudo dd if="$ISO_FILE" of="$DEVICE" bs=4M status=progress oflag=sync
sync

echo "ISO flashed successfully."
echo ""
echo "Next steps:"
echo "1. Use gparted or fdisk to create a data partition in remaining space"
echo "2. Format it as exFAT with label 'FILECHERRY_DATA'"
echo "3. Mount it and create: inputs/, outputs/, config/, logs/, runtime/"
echo ""
echo "Or run: sudo tools/setup_data_partition.sh $DEVICE"

