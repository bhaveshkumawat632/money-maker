#!/usr/bin/env bash
# Stop the Money-Maker Engine.
cd "$(dirname "$0")"
if [ -f data/engine.pid ]; then kill "$(cat data/engine.pid)" 2>/dev/null && echo "engine stopped"; rm -f data/engine.pid; fi
if [ -f data/tracker.pid ]; then kill "$(cat data/tracker.pid)" 2>/dev/null && echo "tracker stopped"; rm -f data/tracker.pid; fi
