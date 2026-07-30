# 💰 MONETIZATION_SETUP — Signup Cheat-Sheet (Paisa Pocket)

Your site is generating articles and is publicly reachable, but **it earns ₹0
until you sign up for the programs below and paste your real IDs.**
No fake IDs are shipped — placeholders are ignored by the engine.

Current live URL (rotates when tunnel restarts): see `data/tunnel.url`
```bash
cat ~/money-maker/data/tunnel.url
```

---

## Where to paste IDs (pick ONE way)

**Option A — ENV vars (recommended, no file edits):**
```bash
# add to ~/.profile or ~/.bashrc, then restart engine.py
export ADSENSE_CLIENT="ca-pub-XXXXXXXXXXXXXXXX"
export ADSENSE_SLOT="1234567890"
export AMAZON_TAG="yourtag-21"
export HOSTING_URL="https://www.hostinger.in/?ref=YOURID"
export MUTUAL_FUND_URL="https://groww.app.link/refe/YOURCODE"
export SOFTWARE_TOOL_URL="https://..."
export WEBHOSTINGPAD_URL="https://..."
```
ENV vars override `config.json`. Empty/unset vars fall back to config placeholders (which render nothing).

**Option B — edit `config.json` → `"affiliate"` block directly.**

New articles pick up IDs automatically on the next 15-min cycle.

---

## 1. Google AdSense (display ads) — biggest earner long-term
- Sign up: https://adsense.google.com → "Get started"
- **Requirement:** AdSense needs a *stable* domain. A rotating
  `trycloudflare.com` URL will NOT be approved. First deploy to a stable
  free host: run `./deploy.sh` (GitHub Pages → `username.github.io/repo`)
  or Netlify, then set that as `site.domain` in config.json.
- After approval, copy **Publisher ID** (`ca-pub-…`) → `ADSENSE_CLIENT`,
  and an ad unit **Slot ID** → `ADSENSE_SLOT`.
- Approval takes days–weeks; needs original content + some traffic. Your 55+
  articles help, but wait until you have a stable domain + Search Console set up.

## 2. Amazon Associates India (product commissions) — easiest to get
- Sign up: https://affiliate.amazon.in (free, approve within ~1–3 days;
  must make 3 sales in 180 days to stay active)
- Copy your **Store/Tracking ID**, e.g. `paisapocket-21` → `AMAZON_TAG`

## 3. Mutual fund / broker referral (₹100–300 per signup)
- **Groww:** app → profile → "Refer & Earn" → copy link → `MUTUAL_FUND_URL`
- **Zerodha:** https://zerodha.com/refer (needs a Zerodha account) → referral link
- Pick one; paste the full referral URL.

## 4. Hosting affiliate (₹500–3000 per sale)
- **Hostinger:** https://www.hostinger.in/affiliates → `HOSTING_URL`
- (Optional) any other program → `SOFTWARE_TOOL_URL` / `WEBHOSTINGPAD_URL`

---

## Free-traffic checklist (already automated / one-time)
- ✅ Cloudflare tunnel: `tunnel.sh` running → site public
- ✅ `./index_now.sh` auto-detects live URL, submits all articles via
  IndexNow (Bing/Yandex/etc). Add to cron: `0 9 * * * ~/money-maker/index_now.sh`
- ⬜ **Google Search Console** (Google dropped anonymous ping): after you have
  a stable domain, add it at https://search.google.com/search-console and
  submit `sitemap.xml` once. This is the #1 traffic unlock.
- ⬜ Stable domain via `./deploy.sh` (GitHub Pages) — needed for AdSense anyway.

**Order of operations:** deploy.sh → Search Console → Amazon Associates →
Groww referral → AdSense (last, once traffic exists).
