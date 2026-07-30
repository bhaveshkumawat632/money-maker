#!/usr/bin/env bash
# Ping search engines so articles get indexed (free traffic). Run daily via cron.
# Auto-detects the live public URL:
#   1. config.json domain if it's a real hosted domain (github.io / netlify / custom)
#   2. data/tunnel.url — but only if the tunnel actually answers (curl 200)
#   3. fallback: grep the latest trycloudflare URL out of data/cf.log
# Uses the IndexNow protocol (Bing/Yandex/Seznam/Naver) — Google & Bing's old
# /ping?sitemap= endpoints were retired, so IndexNow is the reliable free path.
cd "$(dirname "$0")"

alive() { [ "$(curl -s -o /dev/null -w '%{http_code}' -A 'Mozilla/5.0' --max-time 15 "$1/sitemap.xml")" = "200" ]; }

URL=""
# 1) real configured domain wins
DOM=$(python3 -c "import json;print(json.load(open('config.json'))['site']['domain'])" 2>/dev/null)
case "$DOM" in
  *your-domain*|"") ;;
  https://*.github.io*|https://*.netlify.app*|https://*) URL="$DOM" ;;
esac
# 2) live tunnel URL
if [ -z "$URL" ] && [ -f data/tunnel.url ]; then
  T=$(cat data/tunnel.url)
  [ -n "$T" ] && alive "$T" && URL="$T"
fi
# 3) freshest URL from cloudflared log
if [ -z "$URL" ]; then
  T=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' data/cf.log 2>/dev/null | tail -1)
  [ -n "$T" ] && alive "$T" && URL="$T" && echo "$T" > data/tunnel.url
fi

[ -z "$URL" ] && { echo "[index] no live public URL (is tunnel.sh running?)"; exit 1; }
URL="${URL%/}"
HOST="${URL#https://}"; HOST="${HOST#http://}"
echo "[index $(date)] live URL: $URL"

# --- IndexNow key (generated once, must be served from site root) ---
KEY_FILE="data/indexnow.key"
if [ ! -s "$KEY_FILE" ]; then
  (cat /proc/sys/kernel/random/uuid | tr -d '-') > "$KEY_FILE"
fi
KEY=$(cat "$KEY_FILE")
echo "$KEY" > "site/${KEY}.txt"   # key verification file at site root

# --- collect article URLs from sitemap (rewritten to current host) ---
URLS=$(curl -s -A "Mozilla/5.0" "$URL/sitemap.xml" \
  | grep -o '<loc>[^<]*</loc>' | sed -e 's/<[^>]*>//g' \
  | sed -E "s#https?://[^/]+#$URL#" | head -100)
COUNT=$(echo "$URLS" | grep -c . || true)

# --- submit batch to IndexNow (covers Bing, Yandex, Seznam, Naver) ---
if [ "$COUNT" -gt 0 ]; then
  TMP=$(mktemp)
  printf '%s\n' "$URLS" > "$TMP"
  JSON=$(python3 -c '
import json,sys
host,key,f=sys.argv[1],sys.argv[2],sys.argv[3]
urls=[u.strip() for u in open(f) if u.strip()]
print(json.dumps({"host":host,"key":key,"keyLocation":f"https://{host}/{key}.txt","urlList":urls}))
' "$HOST" "$KEY" "$TMP")
  rm -f "$TMP"
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://api.indexnow.org/indexnow" \
    -H "Content-Type: application/json; charset=utf-8" -d "$JSON")
  echo "indexnow ($COUNT urls): HTTP $CODE (200/202 = accepted)"
else
  echo "indexnow: no URLs found in sitemap"
fi

# --- legacy sitemap pings (best-effort; engines may return 404/410 now) ---
SM="$URL/sitemap.xml"
curl -s -A "Mozilla/5.0" "https://www.google.com/ping?sitemap=$SM" -o /dev/null -w "google ping: %{http_code} (deprecated by Google — use Search Console)\n"
curl -s -A "Mozilla/5.0" "https://www.bing.com/ping?sitemap=$SM"   -o /dev/null -w "bing ping:   %{http_code} (deprecated — IndexNow above is what counts)\n"

echo "[index $(date)] done url=$URL count=$COUNT" >> data/index.log
