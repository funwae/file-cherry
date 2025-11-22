# FileCherry First Boot Checklist

This checklist helps verify that FileCherry is working correctly after booting from USB.

## Pre-Boot

- [ ] USB drive has been prepared with ISO and data partition
- [ ] Data partition is formatted as exFAT with label `FILECHERRY_DATA`
- [ ] Data partition contains: `inputs/`, `outputs/`, `config/`, `logs/`, `runtime/`
- [ ] Test files have been placed in `inputs/` (optional, for testing)

## Boot Process

1. Boot from USB drive
2. Wait for system to fully boot (may take 1-2 minutes)
3. System should automatically:
   - Mount the data partition at `/data`
   - Start all services (Ollama, ComfyUI, Orchestrator, UI)
   - Launch Chromium in kiosk mode pointing to `http://localhost:3000`

## Verification Steps

### 1. Check Services

Open a terminal (if kiosk mode allows, or press Ctrl+Alt+F2) and run:

```bash
sudo systemctl status filecherry-orchestrator.service
sudo systemctl status filecherry-ui.service
sudo systemctl status comfyui.service
sudo systemctl status ollama.service
```

All services should show `active (running)`.

### 2. Check Network

Run the network doctor script:

```bash
sudo /opt/filecherry/tools/network-doctor.sh
```

Expected output:
- UI reachable on port 3000
- Orchestrator health endpoint OK on port 8000
- Ollama reachable on port 11434
- ComfyUI reachable on port 8188

### 3. Check Web UI

Open a browser (or verify kiosk mode) and navigate to:
- `http://localhost:3000` - Should show the FileCherry intro screen
- `http://localhost:8000/healthz` - Should return JSON with status

### 4. Test File Inventory

1. Place test files in `inputs/` (if not already done)
2. Refresh the web UI
3. Verify files appear in the inventory display

### 5. Test Job Creation

1. Enter a simple intent in the UI (e.g., "summarize all documents")
2. Click "Continue"
3. Verify plan is generated and displayed
4. Click "Looks good → Run"
5. Monitor job progress
6. Verify outputs appear in `outputs/<job-id>/`

## Troubleshooting

### Services Not Starting

```bash
# Check service logs
sudo journalctl -u filecherry-orchestrator.service -n 50
sudo journalctl -u filecherry-ui.service -n 50

# Restart services
sudo systemctl restart filecherry-orchestrator.service
sudo systemctl restart filecherry-ui.service
```

### Data Partition Not Mounting

```bash
# Check if partition exists
lsblk | grep FILECHERRY_DATA

# Manually mount
sudo mount /dev/disk/by-label/FILECHERRY_DATA /data

# Check mount unit
sudo systemctl status data.mount
```

### UI Not Accessible

```bash
# Check if UI is running
curl http://localhost:3000

# Check UI logs
sudo journalctl -u filecherry-ui.service -n 50

# Verify orchestrator is running
curl http://localhost:8000/healthz
```

### Ollama Not Responding

```bash
# Check Ollama service
sudo systemctl status ollama.service

# Test Ollama API
curl http://localhost:11434/api/tags

# Pull a model if needed
ollama pull phi3:mini
```

### ComfyUI Not Responding

```bash
# Check ComfyUI service
sudo systemctl status comfyui.service

# Check ComfyUI logs
sudo journalctl -u comfyui.service -n 50

# Verify ComfyUI is accessible
curl http://localhost:8188
```

## Post-Boot Configuration

### Model Status

The **phi3:mini model is pre-installed** in the ISO and should be available immediately after boot. No manual download is required.

To verify the model is available:

```bash
ollama list
# Should show phi3:mini in the list
```

If for some reason phi3:mini is missing (shouldn't happen with a properly built ISO), you can pull it:

```bash
ollama pull phi3:mini
```

### Optional: Additional Models

If you want to use additional models (e.g., for embeddings):

```bash
# Embedding model (if using local embeddings)
ollama pull nomic-embed-text
```

### Configure Appliance

Edit `/data/config/appliance.yaml` (if it exists) to customize:
- Default model selection
- Advanced UI toggle
- Network settings

## Success Criteria

- [ ] All services are running
- [ ] Web UI is accessible
- [ ] File inventory displays correctly
- [ ] Job creation works
- [ ] Plan generation works
- [ ] Job execution completes
- [ ] Outputs are saved correctly

## Next Steps

Once verified:
1. Add files to `inputs/` on your regular computer
2. Boot from USB
3. Use the web UI to process files
4. Copy results from `outputs/` back to your computer

