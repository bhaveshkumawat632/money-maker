#!/usr/bin/env bash
# Free public tunnel via Cloudflare (no account needed). Auto-restarts.
# Saves assigned URL to data/tunnel.url. Box must stay on.
# For a stable free domain use GitHub Pages / Netlify (see README).
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
command -v cloudflared >/dev/null 2>&1 || { echo "[tunnel] ERROR: cloudflared not found in PATH"; exit 1; }
echo "[tunnel] starting Cloudflare tunnel (auto-restart)..."
while true; do
  cloudflared tunnel --url http://localhost:8800 > data/cf.log 2>&1 &
  CF_PID=$!
  # capture URL once assigned
  for i in $(seq 1 20); do
    u=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' data/cf.log 2>/dev/null | head -1)
    if [ -n "$u" ]; then echo "$u" > data/tunnel.url; echo "[tunnel] URL: $u"; break; fi
    sleep 1
  done
  wait $CF_PID
  echo "[tunnel] exited ($(date)). restarting in 3s..."
  sleep 3
done
