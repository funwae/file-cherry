# FileCherry Testing Guide

This guide covers two testing approaches:
1. **Local Development Testing** (quickest - test without building ISO)
2. **Full USB Boot Testing** (complete appliance test)

---

## Option 1: Local Development Testing (Recommended First)

This lets you test FileCherry without building an ISO or flashing a USB.

### Prerequisites

- Ubuntu (or WSL2 with Ubuntu)
- Python 3.10+
- Node.js 18+
- Ollama installed and running
- ComfyUI installed (optional, for image processing)

### Step 1: Install Dependencies

```bash
# Clone repo (if not already)
cd /home/hayden/dev/file-cherry

# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# UI dependencies
cd apps/ui
npm install
cd ../..
```

### Step 2: Install & Start Ollama

If Ollama isn't installed:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Start Ollama and pull a model:

```bash
# Start Ollama service (or run: ollama serve)
sudo systemctl start ollama

# Pull a model for planning
ollama pull phi3:mini

# Verify it's running
curl http://localhost:11434/api/tags
```

### Step 3: Install ComfyUI (Optional - for image processing)

If you want to test image pipelines:

```bash
cd /opt
sudo git clone https://github.com/comfyanonymous/ComfyUI.git
sudo chown -R "$USER":"$USER" ComfyUI
cd ComfyUI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start ComfyUI (in a separate terminal)
python main.py --listen 0.0.0.0 --port 8188
```

### Step 4: Set Up Dev Data Directory

```bash
# Create dev-data structure (simulates /data on USB)
mkdir -p dev-data/{inputs,outputs,config,logs,runtime}

# Set environment variable
export FILECHERRY_DATA_DIR=$PWD/dev-data
```

### Step 5: Add Test Files

```bash
# Add some test files to inputs/
# Examples:
echo "This is a test document." > dev-data/inputs/test.txt
# Or copy real files:
# cp ~/Documents/*.pdf dev-data/inputs/
# cp ~/Pictures/*.jpg dev-data/inputs/
```

### Step 6: Start Services

Open **three terminals** (or use `tmux`):

**Terminal 1 - Orchestrator:**
```bash
cd /home/hayden/dev/file-cherry
source .venv/bin/activate
export FILECHERRY_DATA_DIR=$PWD/dev-data
python -m src.orchestrator.main
```

**Terminal 2 - UI:**
```bash
cd /home/hayden/dev/file-cherry/apps/ui
npm run dev
```

**Terminal 3 - ComfyUI (if testing images):**
```bash
cd /opt/ComfyUI
source venv/bin/activate
python main.py --listen 0.0.0.0 --port 8188
```

### Step 7: Test the UI

1. Open `http://localhost:3000` in your browser
2. You should see:
   - File inventory showing files in `dev-data/inputs/`
   - Cody's onboarding (first time only)
   - Input textarea for describing what you want to do

3. Try a simple job:
   - Enter: "Summarize all the documents in inputs"
   - Click "Continue"
   - Review the plan
   - Click "Looks good → Run"
   - Watch the job progress
   - Check `dev-data/outputs/<job-id>/` for results

### Step 8: Verify Services

Check that everything is running:

```bash
# Orchestrator health
curl http://localhost:8000/healthz

# UI
curl http://localhost:3000

# Ollama
curl http://localhost:11434/api/tags

# ComfyUI (if running)
curl http://localhost:8188
```

### Troubleshooting Local Dev

**Orchestrator won't start:**
```bash
# Check Python dependencies
pip list | grep fastapi

# Check logs
python -m src.orchestrator.main 2>&1 | head -20
```

**UI won't start:**
```bash
cd apps/ui
npm install  # Reinstall if needed
npm run dev  # Check for errors
```

**Ollama not responding:**
```bash
# Check if service is running
systemctl status ollama

# Or start manually
ollama serve

# Verify model is installed
ollama list
```

**ComfyUI not responding:**
```bash
# Check if it's running
curl http://localhost:8188

# Check logs in the terminal where you started it
```

---

## Option 2: Full USB Boot Testing

This tests the complete bootable appliance experience.

### Prerequisites

- USB drive (16GB+ recommended)
- VM or physical machine to boot from USB
- Root/sudo access

### Step 1: Build the ISO

```bash
cd /home/hayden/dev/file-cherry

# Make script executable
chmod +x tools/build_iso.sh

# Run build (requires sudo, takes 10-30 minutes)
sudo ./tools/build_iso.sh
```

The ISO will be created at: `build/output/filecherry-<version>.iso`

### Step 2: Flash ISO to USB

**⚠️ WARNING: This will erase the USB drive!**

```bash
# Find your USB device (be very careful!)
lsblk

# Example: if USB is /dev/sdb
sudo ./tools/prepare_usb.sh /dev/sdb build/output/filecherry-*.iso
```

Or manually:
```bash
# Flash ISO
sudo dd if=build/output/filecherry-*.iso of=/dev/sdb bs=4M status=progress

# Sync
sync
```

### Step 3: Create Data Partition

```bash
# Create data partition on USB
sudo ./tools/setup_data_partition.sh /dev/sdb
```

This creates:
- Partition 1: OS (read-only, from ISO)
- Partition 2: Data (exFAT, labeled `FILECHERRY_DATA`)

### Step 4: Initialize Data Partition

Mount the data partition and set it up:

```bash
# Find the partition
lsblk | grep FILECHERRY_DATA

# Mount it (adjust device path as needed)
sudo mkdir -p /mnt/filecherry
sudo mount /dev/disk/by-label/FILECHERRY_DATA /mnt/filecherry

# Create directory structure
sudo mkdir -p /mnt/filecherry/{inputs,outputs,config,logs,runtime}

# Add test files
sudo cp ~/test-files/* /mnt/filecherry/inputs/ 2>/dev/null || true

# Unmount
sudo umount /mnt/filecherry
```

### Step 5: Boot from USB

1. Insert USB into target machine
2. Boot from USB (may need to change BIOS boot order)
3. Wait for system to boot (1-2 minutes)
4. System should automatically:
   - Mount data partition
   - Start all services
   - Launch browser in kiosk mode

### Step 6: Verify Boot

Open a terminal (Ctrl+Alt+F2 if in kiosk mode) and run:

```bash
# Check services
sudo systemctl status filecherry-orchestrator.service
sudo systemctl status filecherry-ui.service
sudo systemctl status comfyui.service
sudo systemctl status ollama.service

# Run network doctor
sudo /opt/filecherry/tools/network-doctor.sh
```

### Step 7: Test the Appliance

1. Open browser to `http://localhost:3000`
2. Verify file inventory shows files from `inputs/`
3. Create a test job
4. Monitor progress
5. Check outputs in `/data/outputs/<job-id>/`

### Troubleshooting USB Boot

See `docs/FIRST_BOOT_CHECKLIST.md` and `docs/TROUBLESHOOTING.md` for detailed troubleshooting.

Quick checks:
```bash
# Check data partition is mounted
ls -la /data

# Check service logs
sudo journalctl -u filecherry-orchestrator.service -n 50
sudo journalctl -u filecherry-ui.service -n 50

# Run network doctor
sudo /opt/filecherry/tools/network-doctor.sh
```

---

## Testing Checklist

### Local Dev Testing
- [ ] All services start without errors
- [ ] UI loads at `http://localhost:3000`
- [ ] File inventory displays files from `dev-data/inputs/`
- [ ] Can create a job with simple intent
- [ ] Plan is generated by Ollama
- [ ] Job executes and completes
- [ ] Outputs appear in `dev-data/outputs/<job-id>/`
- [ ] Cody chat works (if implemented)
- [ ] Onboarding flow appears (first time)

### USB Boot Testing
- [ ] ISO builds successfully
- [ ] USB flashes without errors
- [ ] Data partition is created and formatted
- [ ] System boots from USB
- [ ] All services start automatically
- [ ] Data partition mounts at `/data`
- [ ] UI loads in kiosk mode
- [ ] File inventory works
- [ ] Job creation and execution works
- [ ] Outputs are saved correctly

---

## Next Steps

After successful testing:

1. **Report Issues**: If you find bugs, check `docs/TROUBLESHOOTING.md` first
2. **Improve Documentation**: Update docs based on what you learned
3. **Add Features**: See `docs/PHASES.md` for planned features
4. **Contribute**: PRs welcome! See `README.md` for contribution guidelines

---

## Quick Reference

**Local Dev:**
```bash
export FILECHERRY_DATA_DIR=$PWD/dev-data
source .venv/bin/activate
python -m src.orchestrator.main  # Terminal 1
cd apps/ui && npm run dev         # Terminal 2
```

**USB Boot:**
```bash
sudo ./tools/build_iso.sh
sudo ./tools/prepare_usb.sh /dev/sdX build/output/filecherry-*.iso
sudo ./tools/setup_data_partition.sh /dev/sdX
```

**Diagnostics:**
```bash
sudo /opt/filecherry/tools/network-doctor.sh
filecherry-jobs
filecherry-logs
```

