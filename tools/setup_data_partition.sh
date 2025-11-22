#!/usr/bin/env bash
set -euo pipefail

# tools/setup_data_partition.sh
# Create and format the data partition on a USB device.
#
# Usage: sudo tools/setup_data_partition.sh <device>
# Example: sudo tools/setup_data_partition.sh /dev/sdX

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <device>"
  echo "Example: $0 /dev/sdX"
  exit 1
fi

DEVICE="$1"

if [[ ! -b "$DEVICE" ]]; then
  echo "Error: Device not found: $DEVICE"
  exit 1
fi

echo "WARNING: This will modify partitions on $DEVICE"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Find the last partition number
LAST_PART=$(lsblk -n -o NAME "$DEVICE" | grep -E "${DEVICE##*/}[0-9]+" | tail -1 | sed "s/${DEVICE##*/}//")
if [[ -z "$LAST_PART" ]]; then
  echo "Error: Could not find existing partitions"
  exit 1
fi

# Calculate next partition number
NEXT_PART=$((LAST_PART + 1))
DATA_PART="${DEVICE}${NEXT_PART}"

echo "Creating data partition ${DATA_PART}..."

# Get device size and calculate partition start
DEVICE_SIZE=$(sudo blockdev --getsize64 "$DEVICE")
PART_START=$(sudo parted "$DEVICE" unit s print | grep "^ ${LAST_PART}" | awk '{print $3}' | sed 's/s//')
PART_START=$((PART_START + 1))

# Create partition
sudo parted "$DEVICE" mkpart primary exfat "${PART_START}s" 100%

# Format as exFAT
echo "Formatting partition as exFAT..."
sudo mkfs.exfat -n FILECHERRY_DATA "$DATA_PART"

# Mount and create directories
MOUNT_POINT="/mnt/filecherry-data"
sudo mkdir -p "$MOUNT_POINT"
sudo mount "$DATA_PART" "$MOUNT_POINT"

echo "Creating directory structure..."
sudo mkdir -p "$MOUNT_POINT"/{inputs,outputs,config,logs,runtime}
sudo chmod 755 "$MOUNT_POINT"/{inputs,outputs,config,logs,runtime}

# Create README
sudo tee "$MOUNT_POINT/README.txt" > /dev/null <<EOF
FileCherry Data Partition

This partition contains your files and configuration.

Directories:
- inputs/    - Drop files here for processing
- outputs/   - Processed results appear here
- config/    - Configuration files (advanced)
- logs/      - Application logs
- runtime/   - Internal caches and indices

To use:
1. Plug this USB into your Mac/Windows computer
2. Copy files to inputs/
3. Boot from this USB
4. Follow the on-screen instructions
5. Copy results from outputs/ back to your computer
EOF

sudo umount "$MOUNT_POINT"
sudo rmdir "$MOUNT_POINT"

echo ""
echo "Data partition created successfully!"
echo "Partition: $DATA_PART"
echo "Label: FILECHERRY_DATA"
echo "Format: exFAT"

