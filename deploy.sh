#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
GH_USER="bhaveshkumawat632"
GH_REPO="$GH_USER.github.io"
export GH_TOKEN="${MONEY_MAKER_GH_TOKEN:-}"
if [ -z "$GH_TOKEN" ]; then
  echo "Set MONEY_MAKER_GH_TOKEN env var"
  exit 1
fi
echo "[deploy] building ..."
python3 engine.py rebuild >/dev/null 2>&1 || true
TMP=$(mktemp -d)
cp -r site/. "$TMP/"
cd "$TMP"
git init -q
git config user.email "bot@money-maker.local"
git config user.name "Money-Maker Bot"
git add -A
git commit -q -m "deploy $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git branch -M main
echo "[deploy] pushing ..."
printf "https://%s@github.com\n" "$GH_TOKEN" | git credential fill 2>/dev/null | git push -f "https://x-token-auth@github.com/${GH_USER}/${GH_REPO}.git" main
echo "✅ Done! https://${GH_REPO}"