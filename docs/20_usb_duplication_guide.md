# USB Duplication Guide for FileCherry

Once you have a working ISO (`filecherry-<version>.iso`), this guide explains how to:

1. Flash it to a USB drive.
2. Create the **data partition**.
3. Duplicate sticks.

## 1. Identify the USB Device

1. Insert the target USB stick.
2. Run:
```bash
lsblk
```
Look for a device like `/dev/sdX` with the expected size (e.g., 128G).

> **WARNING:** Double-check. Using the wrong device will erase other disks.

## 2. Flash ISO to USB

From your build host:

```bash
sudo dd if=build/output/filecherry-0.1.0.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

Wait for completion, then:

```bash
sync
```

This writes the ISO partitions (EFI, system, etc.) to the stick.

## 3. Add Data Partition

1. Run `gparted` or `sudo fdisk /dev/sdX`.
2. Shrink the last partition if necessary to free space.
3. Create a new partition in the free space:
   * Type: **exFAT** (for widest Mac/Windows compatibility) or **ext4** if Linux-only.
   * Label: `FILECHERRY_DATA`.

Example (exFAT):

```bash
sudo mkfs.exfat -n FILECHERRY_DATA /dev/sdX3
```

## 4. Seed Data Partition

Mount the new partition:

```bash
sudo mkdir -p /mnt/filecherry-data
sudo mount /dev/sdX3 /mnt/filecherry-data
```

Create expected directories:

```bash
sudo mkdir -p /mnt/filecherry-data/{inputs,outputs,config,logs,runtime}
sudo chown -R "$USER":"$USER" /mnt/filecherry-data
```

You can pre-populate `config/` with defaults and a `README.txt` for users.

## 5. Duplicate Sticks

**Option 1 – Clone With `dd`**

* Once you have a "golden" USB, you can clone it to others:
  ```bash
  sudo dd if=/dev/sdX of=/dev/sdY bs=4M status=progress oflag=sync
  ```
  Where `/dev/sdX` is the **golden** USB and `/dev/sdY` is a blank target.
* After cloning, consider:
  * changing the label of the data partition (optional).
  * clearing any user-specific config if present.

**Option 2 – Clone Only System + Create Fresh Data Partition**

1. `dd` only up to the end of the system partitions (more complex; requires careful partition size tracking).
2. Then create and format `/dev/sdY3` as `FILECHERRY_DATA`.

For small batches, doing `dd` of the entire stick is simpler.

## 6. Testing Each Stick

On each newly created USB:

1. Boot a test machine.
2. Confirm:
   ```bash
   ls /data
   # should show inputs outputs config logs runtime
   ```
3. Run `tools/network-doctor.sh` to confirm core services (once that script is included in the image).

## 7. Labeling & Inventory

Physically label sticks with:

* `FileCherry v0.1.0`
* Date built
* Whether it's **dev** or **prod**.

Keep a spreadsheet of:

* Serial number
* Version
* Customer / owner.

