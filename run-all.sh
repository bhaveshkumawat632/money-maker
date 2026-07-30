#!/usr/bin/env bash
# Master launcher: engine + tracker + free public tunnel. One command, 24/7.
# Stops previous instances first so restarts are clean.
set -e
cd "$(dirname "$0")"

echo "[run-all] stopping any old instances..."
pkill -f "engine.py tracker" 2>/dev/null || true
pkill -f "engine.py$" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 2

echo "[run-all] starting engine + tracker..."
nohup python3 engine.py > data/engine.out 2>&1 &
echo $! > data/engine.pid

echo "[run-all] starting tracker on :8800..."
nohup python3 engine.py tracker > data/tracker.out 2>&1 &
echo $! > data/tracker.pid

echo "[run-all] starting free public Cloudflare tunnel (auto-restart)..."
nohup ./tunnel.sh > data/tunnel.out 2>&1 &
echo $! > data/tunnel.pid

sleep 10
url=$(grep -o 'https://[a-z-]*\.trycloudflare\.com' data/tunnel.out 2>/dev/null | head -1)
echo "=================================================="
echo "✅ Money-Maker Engine LIVE"
echo "   Local : http://localhost:8800"
echo "   Public: ${url:-<tunnel starting, check data/tunnel.out>}"
echo "   Posts : python3 engine.py once   (1 article now)"
echo "   Deploy: edit deploy.sh -> ./deploy.sh  (free *.github.io)"
echo "=================================================="
echo "Stop anytime: ./stop-all.sh"
