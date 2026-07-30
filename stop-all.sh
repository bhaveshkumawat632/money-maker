#!/usr/bin/env bash
# Stop everything started by run-all.sh / start.sh / tunnel.sh.
pkill -f "engine.py tracker" 2>/dev/null && echo "tracker stopped" || true
pkill -f "engine.py$" 2>/dev/null && echo "engine stopped" || true
pkill -f "cloudflared tunnel" 2>/dev/null && echo "tunnel stopped" || true
rm -f data/engine.pid data/tracker.pid data/tunnel.pid
echo "All stopped."
