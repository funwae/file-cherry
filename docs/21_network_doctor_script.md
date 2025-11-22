# Network Doctor Script – tools/network-doctor.sh

This doc contains the final form of `tools/network-doctor.sh`, referenced in other docs. It's designed to run both on **dev machines** and on the **FileCherry appliance** to quickly diagnose networking issues.

## 1. Script Location

- Path: `tools/network-doctor.sh`
- Make executable:
```bash
chmod +x tools/network-doctor.sh
```
Run with:
```bash
bash tools/network-doctor.sh
```
(On appliance you might use `sudo bash /opt/filecherry/tools/network-doctor.sh`.)

## 2. Script Contents

```bash
#!/usr/bin/env bash
set -euo pipefail

# tools/network-doctor.sh
# Quick networking + service health check for FileCherry.

echo "=== FileCherry Network Doctor ==="
echo

DATA_DIR="${FILECHERRY_DATA_DIR:-/data}"

timestamp() { date -Iseconds; }

section() {
  echo
  echo "[$(timestamp)] ---- $* ----"
}

section "Basic system info"
uname -a || true
echo "Hostname: $(hostname || echo 'unknown')"

section "IP addresses"
ip a || true

section "Routing table"
ip route || true

section "Listening ports (3000, 8000, 8188, 11434)"
ss -tulnp | grep -E '3000|8000|8188|11434' || echo "No expected ports open."

section "Ping test (optional, may fail if offline)"
if ping -c 1 1.1.1.1 >/dev/null 2>&1; then
  echo "Ping to 1.1.1.1 OK."
else
  echo "Ping to 1.1.1.1 FAILED (offline or blocked)."
fi

# --- UI check ---
section "UI (port 3000)"
if curl -sS --max-time 3 http://127.0.0.1:3000 >/dev/null 2>&1; then
  echo "UI reachable on http://127.0.0.1:3000"
else
  echo "UI NOT reachable on http://127.0.0.1:3000"
fi

# --- Orchestrator check ---
section "Orchestrator (port 8000)"
if curl -sS --max-time 3 http://127.0.0.1:8000/healthz >/dev/null 2>&1; then
  echo "Orchestrator health endpoint OK."
else
  echo "Orchestrator NOT responding on /healthz."
fi

# --- Ollama check ---
section "Ollama (port 11434)"
if curl -sS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama API reachable; models:"
  curl -sS http://127.0.0.1:11434/api/tags | jq '.models[].name' 2>/dev/null || echo "(jq not installed, raw output suppressed)"
else
  echo "Ollama NOT reachable on 127.0.0.1:11434"
fi

# --- ComfyUI check ---
section "ComfyUI (port 8188)"
if curl -sS --max-time 3 http://127.0.0.1:8188 >/dev/null 2>&1; then
  echo "ComfyUI reachable on http://127.0.0.1:8188"
else
  echo "ComfyUI NOT reachable on http://127.0.0.1:8188"
fi

# --- Data dir check ---
section "Data directory"
echo "Using DATA_DIR=$DATA_DIR"
if [ -d "$DATA_DIR" ]; then
  echo "Contents of $DATA_DIR:"
  ls -1 "$DATA_DIR" || true
else
  echo "Data directory $DATA_DIR does NOT exist."
fi

section "Recent logs (if present)"
if [ -d "$DATA_DIR/logs" ]; then
  for f in "$DATA_DIR"/logs/*.log; do
    [ -e "$f" ] || continue
    echo "--- Tail of $f ---"
    tail -n 20 "$f" || true
  done
else
  echo "No logs directory at $DATA_DIR/logs"
fi

echo
echo "=== Network Doctor finished ==="
```

## 3. Usage

* Ask any tester or customer to run:
  ```bash
  sudo bash /opt/filecherry/tools/network-doctor.sh > network-dump.txt
  ```
* Have them send you `network-dump.txt`.
* Use it to:
  * confirm services are running
  * confirm ports are open
  * see logs without needing full SSH debugging.

