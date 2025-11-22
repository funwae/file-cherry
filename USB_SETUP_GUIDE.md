# USB Setup Guide - Quick Start

## Option 1: Etcher/Rufus (Recommended - Easier)

### Step 1: Flash ISO with Etcher or Rufus

**Using Balena Etcher:**
1. Download from https://www.balena.io/etcher
2. Open Etcher
3. Click "Flash from file" → Select `build/output/filecherry-0.1.0.iso`
4. Click "Select target" → Choose your 32GB USB drive
5. Click "Flash!" and wait

**Using Rufus (Windows):**
1. Download from https://rufus.ie
2. Open Rufus
3. Select your USB drive
4. Click "SELECT" → Choose `build/output/filecherry-0.1.0.iso`
5. Use default settings (GPT, UEFI)
6. Click "START" and wait

### Step 2: Create Data Partition

After flashing, you need to create the data partition that users can access on Mac/Windows:

```bash
# Find your USB device (usually /dev/sdb or /dev/sdc)
lsblk

# Create the data partition (replace /dev/sdX with your device)
sudo ./tools/setup_data_partition.sh /dev/sdX
```

This will:
- Create a new partition in the remaining space
- Format it as exFAT (readable on Mac/Windows)
- Label it `FILECHERRY_DATA`
- Create the directory structure (inputs/, outputs/, etc.)

## Option 2: All-in-One Script (Linux Only)

If you're on Linux and want to do it all at once:

```bash
# Find your USB device
lsblk

# Flash ISO and create data partition
sudo ./tools/prepare_usb.sh build/output/filecherry-0.1.0.iso /dev/sdX
sudo ./tools/setup_data_partition.sh /dev/sdX
```

## Verification

After setup, verify:

```bash
# Check partitions
lsblk /dev/sdX

# You should see:
# - Partition 1: ISO system (read-only)
# - Partition 2: FILECHERRY_DATA (exFAT, writable)

# Mount and check data partition
sudo mkdir -p /mnt/test
sudo mount /dev/sdX2 /mnt/test  # Adjust partition number
ls /mnt/test
# Should show: inputs/, outputs/, config/, logs/, runtime/, README.txt
sudo umount /mnt/test
```

## What You Get

After setup, your USB drive will have:

1. **System Partition** (read-only, ~18GB)
   - FileCherry OS
   - Bootable from USB
   - Contains all services and code

2. **Data Partition** (writable, remaining space)
   - Label: `FILECHERRY_DATA`
   - Format: exFAT (readable on Mac/Windows)
   - Contains: inputs/, outputs/, config/, logs/, runtime/
   - Users can access this from their normal computer

## Next Steps

1. Boot from the USB on a test machine
2. Verify services start automatically
3. Access UI at http://localhost:3000
4. Test with files in inputs/

