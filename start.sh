#!/usr/bin/env bash
# Money-Maker Engine launcher — runs the publisher + tracker 24/7.
set -e
cd "$(dirname "$0")"

echo "[money-maker] starting engine loop (articles every 60 min)..."
nohup python3 engine.py > data/engine.out 2>&1 &
echo $! > data/engine.pid

echo "[money-maker] starting tracker server on :8800..."
nohup python3 engine.py tracker > data/tracker.out 2>&1 &
echo $! > data/tracker.pid

echo "[money-maker] both running. Logs: data/engine.out, data/tracker.out"
echo "[money-maker] stop with: ./stop.sh"
