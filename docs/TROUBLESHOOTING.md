# Troubleshooting Guide

Common issues and solutions for FileCherry appliance.

## Services Not Starting

### Check Service Status

```bash
sudo systemctl status filecherry-orchestrator.service
sudo systemctl status filecherry-ui.service
sudo systemctl status comfyui.service
sudo systemctl status ollama.service
```

### View Service Logs

```bash
sudo journalctl -u filecherry-orchestrator.service -n 50
sudo journalctl -u filecherry-ui.service -n 50
```

### Restart Services

```bash
sudo systemctl restart filecherry-orchestrator.service
sudo systemctl restart filecherry-ui.service
```

## Data Partition Not Mounting

### Check Partition Exists

```bash
lsblk | grep FILECHERRY_DATA
```

### Manually Mount

```bash
sudo mount /dev/disk/by-label/FILECHERRY_DATA /data
```

### Check Mount Unit

```bash
sudo systemctl status data.mount
sudo systemctl start data.mount
```

## UI Not Accessible

### Check Port

```bash
curl http://localhost:3000
ss -tulnp | grep 3000
```

### Check UI Logs

```bash
sudo journalctl -u filecherry-ui.service -n 50
filecherry-logs --component ui
```

### Verify Orchestrator

```bash
curl http://localhost:8000/healthz
```

## Ollama Not Responding

### Check Service

```bash
sudo systemctl status ollama.service
```

### Test API

```bash
curl http://localhost:11434/api/tags
```

### Pull Models

```bash
ollama pull phi3:mini
ollama pull nomic-embed-text
```

### Check Logs

```bash
sudo journalctl -u ollama.service -n 50
```

## ComfyUI Not Responding

### Check Service

```bash
sudo systemctl status comfyui.service
```

### Test API

```bash
curl http://localhost:8188
```

### Check Logs

```bash
sudo journalctl -u comfyui.service -n 50
```

### Verify Installation

```bash
ls -la /opt/ComfyUI
```

## Job Failures

### List Jobs

```bash
filecherry-jobs
```

### View Job Details

```bash
filecherry-job <job-id>
```

### View Job Logs

```bash
filecherry-logs --job-id <job-id>
```

### Check Manifest

```bash
cat /data/outputs/<job-id>/manifest.json | jq
```

## Network Issues

### Run Network Doctor

```bash
sudo /opt/filecherry/tools/network-doctor.sh
```

### Check IP Address

```bash
ip a
```

### Test Connectivity

```bash
ping -c 3 1.1.1.1
```

## Permission Issues

### Check Data Directory Permissions

```bash
ls -la /data
```

### Fix Permissions

```bash
sudo chown -R filecherry:filecherry /data
sudo chmod -R 755 /data
```

## Log Files Growing Too Large

### Rotate Logs Manually

```bash
sudo /opt/filecherry/tools/rotate_logs.sh
```

### Check Log Size

```bash
du -sh /data/logs
```

### Clear Old Logs

```bash
sudo find /data/logs -name "*.log.*" -mtime +30 -delete
```

## Performance Issues

### Check System Resources

```bash
htop
nvidia-smi  # If GPU available
```

### Check Disk Space

```bash
df -h
```

### Check Memory

```bash
free -h
```

## Getting Help

1. Run the network doctor script and save output:
   ```bash
   sudo /opt/filecherry/tools/network-doctor.sh > diagnostics.txt
   ```

2. Collect job information:
   ```bash
   filecherry-jobs > jobs.txt
   ```

3. Collect recent logs:
   ```bash
   filecherry-logs --lines 100 > recent-logs.txt
   ```

4. Include these files when reporting issues.

