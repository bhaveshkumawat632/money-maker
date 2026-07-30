#!/usr/bin/env bash
# Stop the Cloudflare tunnel (kills cloudflared processes).
pkill -f "cloudflared tunnel" 2>/dev/null && echo "tunnel stopped" || echo "no tunnel running"
