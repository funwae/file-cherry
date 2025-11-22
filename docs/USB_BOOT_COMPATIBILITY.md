# USB Boot Compatibility Guide

## Overview

FileCherry ISO is built as a **live system** (not an installer). It boots directly into the OS without requiring installation. The ISO is configured as a **hybrid ISO** which means it can be flashed to USB using standard tools like Balena Etcher or Rufus.

## What Makes It Work

### 1. Live System (Not Installer)

- ✅ Based on Ubuntu Desktop ISO (live system)
- ✅ Boots directly into FileCherry OS
- ✅ No installation required
- ✅ Runs from USB in read-only mode (with writable data partition)

### 2. Hybrid ISO Configuration

For the ISO to work with Etcher/Rufus, it must be **hybrid bootable**:

- **MBR (Master Boot Record)**: For BIOS/Legacy boot
- **GPT (GUID Partition Table)**: For UEFI boot
- **El Torito boot sectors**: For CD/DVD boot

The build script uses:
- `-isohybrid-mbr` - Makes ISO bootable from USB (BIOS)
- `-isohybrid-gpt-basdat` - Adds GPT support (UEFI)

### 3. Required Build Dependencies

To create a hybrid ISO, you need:

```bash
sudo apt install syslinux-utils xorriso
```

The `syslinux-utils` package provides `isohdpfx.bin` which is required for hybrid MBR.

## Flashing Methods

### ✅ Balena Etcher

1. Download Balena Etcher
2. Select the FileCherry ISO
3. Select your USB drive
4. Flash

**Works out of the box** if ISO is hybrid (which it should be).

### ✅ Rufus

1. Download Rufus
2. Select the FileCherry ISO
3. Select your USB drive
4. Use default settings (GPT partition scheme, UEFI target)
5. Start

**Works out of the box** if ISO is hybrid.

### ✅ dd (Linux/Mac)

```bash
sudo dd if=filecherry-0.1.0.iso of=/dev/sdX bs=4M status=progress
sync
```

**Works** because hybrid ISO can be directly written to USB.

### ✅ Ventoy

1. Install Ventoy on USB
2. Copy ISO file to USB
3. Boot from USB and select ISO

**Works** - Ventoy can boot any ISO file.

## Verification

After building, verify the ISO is hybrid:

```bash
# Check if ISO is bootable
file filecherry-0.1.0.iso
# Should show: "bootable"

# Check hybrid configuration
xorriso -indev filecherry-0.1.0.iso -report_el_torito as_mkisofs | grep -i hybrid
```

## Troubleshooting

### ISO Not Booting from USB

1. **Check if hybrid MBR was added:**
   ```bash
   # During build, look for:
   # "✓ Configuring hybrid ISO (bootable from USB with Etcher/Rufus)"
   ```

2. **Verify syslinux-utils is installed:**
   ```bash
   dpkg -l | grep syslinux-utils
   ```

3. **Rebuild with syslinux-utils installed:**
   ```bash
   sudo apt install syslinux-utils
   sudo ./tools/build_iso.sh
   ```

### Etcher/Rufus Says "Not Bootable"

- The ISO might not have hybrid MBR
- Rebuild with `syslinux-utils` installed
- Check build logs for hybrid configuration messages

### Boots but Shows "No Bootable Device"

- BIOS/UEFI boot order might be wrong
- Try disabling Secure Boot
- Try switching between UEFI and Legacy BIOS mode

## Summary

✅ **FileCherry ISO is a live system** (boots directly, no installation)
✅ **Works with Etcher/Rufus** if built with `syslinux-utils` installed
✅ **Hybrid ISO** supports both BIOS and UEFI boot
✅ **Ready to flash** - just use your preferred tool

The build script automatically configures hybrid boot if `isohdpfx.bin` is found (from `syslinux-utils` package).

