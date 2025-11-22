# Networking Guide – Making FileCherry Networking Work (Dev & Appliance)

This doc is the **step-by-step networking cookbook** for FileCherry, focusing on:

- making sure services are reachable on `localhost`
- exposing them on LAN when needed
- debugging when things "just don't connect".

It covers Ubuntu dev and the bootable appliance.

## 1. Mental Model

There are three key network paths:

1. **UI → Orchestrator / APIs**
   - UI (port 3000) → Orchestrator API (e.g. 8000).
2. **Orchestrator → Services**
   - Orchestrator → Ollama (port 11434).
   - Orchestrator → ComfyUI (port 8188).
3. **Remote Access (optional)**
   - Your laptop or another machine → UI / APIs over LAN.

We always start by making sure **localhost networking** works, then open things to LAN if needed.

## 2. Basic Connectivity Checklist (Ubuntu Dev)

### 2.1 Is the interface up?

```bash
ip a
```

Look for an interface like `eth0`, `enp3s0`, or `wlan0` with an IP (e.g. `192.168.x.x`). If there's no IP, use `nmcli` or your network manager to connect to Wi-Fi or DHCP.

### 2.2 Is the UI running?

```bash
curl -I http://localhost:3000
```

You should see an HTTP response (e.g. `HTTP/1.1 200 OK`).

If not:

```bash
ps aux | grep node
systemctl status filecherry-ui  # on appliance / systemd dev
```

Fix any crashes, then re-run `curl`.

### 2.3 Is the Orchestrator running?

```bash
curl -I http://localhost:8000/healthz
```

(Replace with actual orchestrator port.)

If it fails:

```bash
systemctl status filecherry-orchestrator
tail -n 100 /data/logs/orchestrator.log
```

## 3. Ollama Networking

### 3.1 Verify Ollama is Running

```bash
systemctl status ollama
journalctl -u ollama --no-pager --since "5 minutes ago"
```

The official troubleshooting docs recommend using `journalctl -u ollama` to inspect logs on Linux.

### 3.2 Test Local API

```bash
curl http://127.0.0.1:11434/api/tags
```

You should see JSON listing installed models. If that fails:

* Service may not be running.
* Port may be blocked (rare on localhost).
* Installation may not have completed.

### 3.3 Exposing Ollama on LAN (Optional)

By default, Ollama binds to `127.0.0.1:11434`.

To allow other machines on your LAN to reach it, set `OLLAMA_HOST`:

1. Create or edit systemd override:

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

2. Reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

3. Confirm:

```bash
ss -tulnp | grep 11434
# should show 0.0.0.0:11434 or your LAN IP
```

Now from another machine on the same network:

```bash
curl http://<filecherry-ip>:11434/api/tags
```

If you want internet-exposed access, you'd also need router port forwarding and firewall adjustments.

## 4. ComfyUI Networking

### 4.1 Check Service

```bash
systemctl status comfyui
journalctl -u comfyui --no-pager --since "5 minutes ago"
```

### 4.2 Test Local

```bash
curl -I http://127.0.0.1:8188
```

If you get HTTP output, ComfyUI is listening.

### 4.3 Listen on All Interfaces

In the systemd service, ensure:

```ini
ExecStart=/opt/ComfyUI/venv/bin/python main.py --listen 0.0.0.0 --port 8188
```

Restart service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart comfyui
```

Verify:

```bash
ss -tulnp | grep 8188
```

Now UI and orchestrator can both call ComfyUI, and optionally you can hit it from another machine if allowed by firewall.

## 5. Firewall & UFW

On Ubuntu, if `ufw` is enabled, it might block external access.

Check status:

```bash
sudo ufw status
```

* If it's **inactive**, then it's not blocking anything.
* If **active**, allow specific ports:

```bash
sudo ufw allow 3000/tcp   # FileCherry UI
sudo ufw allow 8000/tcp   # Orchestrator (optional external)
sudo ufw allow 11434/tcp  # Ollama (if needed on LAN)
sudo ufw allow 8188/tcp   # ComfyUI (if needed on LAN)
```

For an **appliance intended to be local-only**, we can keep `ufw` enabled but only open the necessary ports.

## 6. Debugging "UI Not Loading"

Symptoms: Boot appliance, but monitor shows blank screen, or browser shows "cannot connect".

Checklist:

1. **Is the browser/kiosk running?**
   ```bash
   ps aux | grep chromium
   systemctl status kiosk-browser  # if using a kiosk service
   ```
2. **Is the UI service alive?**
   ```bash
   systemctl status filecherry-ui
   curl -I http://localhost:3000
   ```
3. **Is the orchestrator required for UI to start?**
   * If UI depends on orchestrator health:
     * check orchestrator logs:
       ```bash
       systemctl status filecherry-orchestrator
       tail -n 100 /data/logs/orchestrator.log
       ```
4. **Check ports:**
   ```bash
   ss -tulnp | grep -E '3000|8000|8188|11434'
   ```
   Make sure each expected service is actually listening.
5. **Overlapping ports / conflicts**
   * If some other service is using `3000`, you'll see multiple lines.
   * Change FileCherry UI port in `config/appliance.yaml` and systemd unit if needed.

## 7. Debugging Networking from Cursor / WSL

If you're developing FileCherry in WSL and using Cursor, sometimes AI indexing or HTTP calls fail due to networking quirks.

Tips:

1. Run Cursor's **network diagnostics** from settings whenever you see "unable to reach service" or indexing stalls.
2. Switch HTTP compatibility mode from HTTP/2 to HTTP/1.1 if diagnostics show HTTP/2 issues.
3. Use `curl` **inside WSL** to test `http://localhost:3000` and `http://localhost:8000/healthz`. If this works but Cursor complains, it's likely an IDE/network config, not your services.

## 8. LAN Access to FileCherry UI

If you want to open the FileCherry web UI from another machine:

1. Ensure the machine has a LAN IP:
   ```bash
   ip a | grep inet
   # e.g., 192.168.1.50
   ```
2. Configure UI to bind `0.0.0.0` instead of `127.0.0.1`:
   * In UI service:
     ```ini
     ExecStart=/usr/bin/node server.js --host 0.0.0.0 --port 3000
     ```
3. Open `3000/tcp` in `ufw` (if enabled):
   ```bash
   sudo ufw allow 3000/tcp
   ```
4. On another machine, open:
   ```
   http://192.168.1.50:3000
   ```

## 9. Quick "It Must Work" Script

For dev, create `tools/network-doctor.sh` (see [Network Doctor Script](21_network_doctor_script.md)):

Run:

```bash
bash tools/network-doctor.sh
```

It gives a single snapshot of what's working and what's not.

## 10. When All Else Fails

* Restart services:
  ```bash
  sudo systemctl restart filecherry-orchestrator filecherry-ui comfyui ollama
  ```
* Check logs under `/data/logs/`.
* Tighten your scope: verify each component *locally* before worrying about cross-machine access.

Once you follow this doc end-to-end, you should be able to:

* get FileCherry services running on Ubuntu dev
* boot the USB appliance and have the UI reachable
* expose services on LAN when needed
* debug the tricky "nothing is connecting" situations.

