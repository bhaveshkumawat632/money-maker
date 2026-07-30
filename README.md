# 💸 Paisa Pocket — Money-Maker Engine (Passive Income, Hindi, ₹0)

A 24/7 automated **Hindi** content engine that publishes money/finance guides
with affiliate links + ads + newsletter + a savings calculator. Runs on your
box, costs nothing, and keeps producing articles every hour — fully unattended.

> ⚠️ HONEST: software automates the *work*. Paying passive income still needs
> (1) a public URL, (2) your affiliate/AdSense IDs, (3) traffic. No "guaranteed
> income" exists — anyone claiming that is a scam.

## ✅ What's built & LIVE right now
- Hindi articles auto-published every 60 min (clean, ₹-examples, SEO-structured).
- Modern site: nav, hero, article cards, **Savings Calculator (₹)**, **Newsletter**,
  affiliate buttons, ad slots, related-posts, RSS, sitemap, JSON-LD, OG tags.
- **AdSense-ready legal pages**: Privacy, Disclaimer, About, Contact, Live Dashboard.
- Free public URL via Cloudflare tunnel (no domain purchase needed).
- Traffic tracker: impressions / leads counted live (`/stats.json`, Dashboard).

## 🚀 Run it (one command)
```bash
cd /home/junglee01/money-maker
./run-all.sh          # engine + tracker + free public tunnel, 24/7
# prints your public https://*.trycloudflare.com URL
```
Stop: `./stop-all.sh`

## 🌐 Permanent FREE domain (GitHub Pages) — **Part A**
1. Free GitHub account → create repo `<you>.github.io`.
2. Edit `deploy.sh`: set `GH_USER`, paste a token (repo scope).
3. `./deploy.sh` → live forever at `https://<you>.github.io`.
Then set `config.json → site.domain` to that URL and re-run `./deploy.sh` once.

(Options B/C also work: Netlify Drop = drag `site/`; or keep the tunnel.)

## 💰 Turn on earnings (Part B) — paste your IDs in `config.json`
| Field | Where to get | Effect |
|---|---|---|
| `affiliate.amazon_tag` | amazon.in Associates | 🛒 Amazon.in button in every post |
| `affiliate.mutual_fund_url` | your Groww/Zerodha link | 📈 Invest CTA |
| `affiliate.hosting_url` | your Hostinger/bigrock link | 🌐 Hosting CTA |
| `affiliate.adsense_client` + `adsense_slot` | AdSense account | real ads render |

Until set, placeholder slots show (no revenue yet — expected).

## ⚙️ Config (`config.json`)
- `engine.language`: `hindi` (default) — UI + content in Hindi.
- `engine.content_mode`: `template` (reliable, instant, ₹-rich Hindi) or
  `ollama` (AI prose if you have a fast model; falls back to template).
- `engine.words_per_article`, `run_every_minutes`, `max_posts`.
- `topics[]`: Hindi topics (20 included; add more for longer un-repeated runs).

## 🛠 Commands
```bash
python3 engine.py          # 24/7 loop (publishes now, then hourly)
python3 engine.py once     # one article now
python3 engine.py rebuild   # re-render site (no new article)
python3 engine.py tracker  # tracker server on :8800
./run-all.sh / ./stop-all.sh
./tunnel.sh / ./stop-tunnel.sh
```

## 📊 Live stats
`http://localhost:8800/stats.json` or the **Live Dashboard** page.

---
Built by Hermes. No API cost, no purchase, fully yours. Paste affiliate IDs → earn.
