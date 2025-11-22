#!/usr/bin/env bash
# tools/network-doctor.sh
# Diagnostic script for FileCherry appliance networking and services.

set -euo pipefail

DATA_DIR="${FILECHERRY_DATA_DIR:-/data}"

section() {
  echo
  echo "=== $* ==="
}

echo "FileCherry Network Doctor"
echo "========================"
echo "Timestamp: $(date)"
echo

section "System information"
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
  ORCHESTRATOR_STATUS=$(curl -sS http://127.0.0.1:8000/healthz 2>/dev/null || echo "{}")
  echo "Response: $ORCHESTRATOR_STATUS"
else
  echo "Orchestrator NOT responding on /healthz."
fi

# --- Ollama check ---
section "Ollama (port 11434)"
if curl -sS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama API reachable; models:"
  curl -sS http://127.0.0.1:11434/api/tags 2>/dev/null | \
    python3 -m json.tool 2>/dev/null | \
    grep -E '"name"' | head -5 || echo "(Could not parse model list)"
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

# --- Systemd services ---
section "Systemd service status"
systemctl is-active filecherry-orchestrator.service 2>/dev/null && \
  echo "filecherry-orchestrator: active" || \
  echo "filecherry-orchestrator: inactive/failed"
systemctl is-active filecherry-ui.service 2>/dev/null && \
  echo "filecherry-ui: active" || \
  echo "filecherry-ui: inactive/failed"
systemctl is-active comfyui.service 2>/dev/null && \
  echo "comfyui: active" || \
  echo "comfyui: inactive/failed"
systemctl is-active ollama.service 2>/dev/null && \
  echo "ollama: active" || \
  echo "ollama: inactive/failed"

# --- Data dir check ---
section "Data directory"
echo "Using DATA_DIR=$DATA_DIR"
if [ -d "$DATA_DIR" ]; then
  echo "Contents of $DATA_DIR:"
  ls -1 "$DATA_DIR" || true
  echo
  echo "Inputs directory:"
  ls -1 "$DATA_DIR/inputs" 2>/dev/null | head -10 || echo "(empty or not accessible)"
else
  echo "Data directory $DATA_DIR does NOT exist."
fi

section "Recent logs (if present)"
if [ -d "$DATA_DIR/logs" ]; then
  for f in "$DATA_DIR"/logs/*.log; do
    [ -e "$f" ] || continue
    echo "--- Tail of $(basename "$f") ---"
    tail -n 20 "$f" || true
  done
else
  echo "No logs directory at $DATA_DIR/logs"
fi

# --- Journal logs ---
section "Recent systemd journal entries"
journalctl -u filecherry-orchestrator.service -n 10 --no-pager 2>/dev/null || true
journalctl -u filecherry-ui.service -n 10 --no-pager 2>/dev/null || true

echo
echo "=== Network Doctor finished ==="

