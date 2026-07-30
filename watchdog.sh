#!/usr/bin/env bash
# Watchdog: keeps engine + tracker + tunnel alive 24/7. Run via cron every 5 min.
# If any piece is missing, restart it. Non-stop money machine.
cd "$(dirname "$0")"

alive() { pgrep -f "$1" >/dev/null 2>&1; }

if ! alive "engine.py$"; then
  echo "[watchdog $(date)] engine down -> restart" >> data/watchdog.log
  nohup python3 engine.py >> data/engine.out 2>&1 &
fi

if ! alive "engine.py tracker"; then
  echo "[watchdog $(date)] tracker down -> restart" >> data/watchdog.log
  nohup python3 engine.py tracker >> data/tracker.out 2>&1 &
fi

if ! alive "cloudflared tunnel"; then
  echo "[watchdog $(date)] tunnel down -> restart" >> data/watchdog.log
  nohup ./tunnel.sh >> data/tunnel.out 2>&1 &
fi
echo "[watchdog $(date)] ok" >> data/watchdog.log
