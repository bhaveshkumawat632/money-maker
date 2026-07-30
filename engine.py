#!/usr/bin/env python3
"""
Money-Maker Engine — a 24/7 passive-income content machine.

What it does, on a loop (default every 60 min):
  1. Picks the next niche topic.
  2. Generates an SEO article with a local Ollama model (FREE, no API cost).
  3. Injects affiliate links + AdSense slots into the article.
  4. Publishes it to a static blog (index.html + per-post pages + sitemap.xml).
  5. Tracks traffic (impressions/clicks) via a tiny tracker + log.

It is HONEST software: it automates the *work*, not the *guarantee*.
Real money requires: (a) you host the site on a domain, (b) you sign up for
affiliate programs + AdSense, (c) traffic actually arrives. The engine never
stops producing — that part is fully passive.

Pure Python stdlib. No pip installs. Runs on CPU.
"""

import json
import os
import re
import html
import time
import random
import urllib.request
import urllib.error
import datetime
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
SITE_DIR = ROOT / "site"
POSTS_DIR = SITE_DIR / "posts"
ASSETS_DIR = SITE_DIR / "assets"
DATA_DIR = ROOT / "data"
LOG_PATH = DATA_DIR / "engine.log"
STATS_PATH = DATA_DIR / "stats.json"
POSTS_DB = DATA_DIR / "posts.json"

SITE_DIR.mkdir(parents=True, exist_ok=True)
POSTS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
FEATURED_DIR = ASSETS_DIR / "featured"
FEATURED_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            log(f"WARN: could not parse {path}: {e}; using default")
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
cfg = load_json(CONFIG_PATH, {})
engine_cfg = cfg.get("engine", {})
site_cfg = cfg.get("site", {})
affiliate = cfg.get("affiliate", {})

# --- ENV overrides for monetization IDs (paste real IDs, no code edits) ---
# Export these before running the engine (or put them in ~/.profile):
#   ADSENSE_CLIENT, ADSENSE_SLOT, AMAZON_TAG, HOSTING_URL,
#   WEBHOSTINGPAD_URL, SOFTWARE_TOOL_URL, MUTUAL_FUND_URL
_ENV_AFFILIATE_MAP = {
    "adsense_client": "ADSENSE_CLIENT",
    "adsense_slot": "ADSENSE_SLOT",
    "amazon_tag": "AMAZON_TAG",
    "hosting_url": "HOSTING_URL",
    "webhostingpad_url": "WEBHOSTINGPAD_URL",
    "software_tool_url": "SOFTWARE_TOOL_URL",
    "mutual_fund_url": "MUTUAL_FUND_URL",
}
for _cfg_key, _env_key in _ENV_AFFILIATE_MAP.items():
    _val = os.environ.get(_env_key, "").strip()
    if _val:
        affiliate[_cfg_key] = _val

topics = cfg.get("topics", [])
MODEL = engine_cfg.get("model", "hermes-1.5b")
OLLAMA_URL = engine_cfg.get("ollama_url", "http://127.0.0.1:11434")
WORDS = engine_cfg.get("words_per_article", 800)
MAX_POSTS = engine_cfg.get("max_posts", 500)
RUN_EVERY = engine_cfg.get("run_every_minutes", 60)
NICHE = cfg.get("niche", "general")

SITE_NAME = site_cfg.get("name", "Money Maker Blog")
DOMAIN = site_cfg.get("domain", "https://your-domain.com")
TAGLINE = site_cfg.get("tagline", "")
LANG = site_cfg.get("language", "en")
CURRENCY = site_cfg.get("currency", "₹")
COUNTRY = site_cfg.get("country", "IN")
KEYWORDS = "पैसा कमाएं, निवेश, SIP, म्यूचुअल फंड, बचत, टैक्स, बजट, भारत में फाइनेंस, पैसा बचाएं, ऑनलाइन कमाएं"
ENGINE_LANG = engine_cfg.get("language", "english")


# --------------------------------------------------------------------------- #
# Ollama content generation
# --------------------------------------------------------------------------- #
def slugify(text: str) -> str:
    """URL-safe slug. Transliterates Devanagari to latin for clean URLs."""
    text = text.strip().lower()
    # Transliterate common Devanagari -> latin (covers most Hindi topics).
    if re.search(r"[\u0900-\u097f]", text):
        try:
            from unidecode import unidecode
            text = unidecode(text)
        except Exception:
            # crude fallback map if unidecode missing
            tr = {
                "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
                "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "क": "k", "ख": "kh",
                "ग": "g", "घ": "gh", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh",
                "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t",
                "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p", "फ": "ph",
                "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l",
                "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h", "क्ष": "ksh",
                "त्र": "tr", "ज्ञ": "gy", "ट्र": "tr", "ं": "", "ः": "", "ा": "a",
                "ि": "i", "ी": "i", "ु": "u", "ू": "u", "े": "e", "ै": "ai",
                "ो": "o", "ौ": "au", "्": "", "ॉ": "o", "ॅ": "e",
            }
            out = []
            for ch in text:
                out.append(tr.get(ch, ch))
            text = "".join(out)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:80] or "post"



# --------------------------------------------------------------------------- #
# Content quality checker
# --------------------------------------------------------------------------- #
def quality_score(md_text: str) -> dict:
    """Simple content quality check. Returns dict with scores and issues."""
    results = {"score": 100, "issues": [], "readability": {}, "keywords": {}}
    
    # Word count check
    words = md_text.split()
    wc = len(words)
    if wc < 300:
        results["issues"].append("Too short (<300 words)")
        results["score"] -= 20
    elif wc < 400:
        results["issues"].append("Could be longer for better depth")
        results["score"] -= 5
    
    # Heading density
    h2_count = md_text.count("## ")
    h3_count = md_text.count("### ")
    if h2_count < 3:
        results["issues"].append("Add more sections (## H2 headings)")
        results["score"] -= 10
    
    # Bullet list check
    bullet_count = len([l for l in md_text.split("\n") if l.strip().startswith("- ")])
    if bullet_count < 3:
        results["issues"].append("Add bullet points for readability")
        results["score"] -= 5
    
    # Avoid ALL CAPS (clickbait detection)
    caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / max(len(words), 1)
    if caps_ratio > 0.15:
        results["issues"].append("Too many ALL CAPS words — may look like clickbait")
        results["score"] -= 10
    
    # Readability: Flesch-like (simple Hindi/English mix check)
    sentences = md_text.count("\n\n") + 1
    if sentences > 0:
        avg_words_per_sentence = wc / sentences
        results["readability"] = {
            "words": wc,
            "sentences": sentences,
            "avg_words_per_sentence": round(avg_words_per_sentence, 1),
            "headings": h2_count + h3_count,
            "bullets": bullet_count,
        }
    
    results["score"] = max(0, min(100, results["score"]))
    return results

# Fallback model chain — if one model fails or OOM, try next
MODEL_CHAIN = ["qwen2.5:7b", "deepseek-hermes:7b", "deepseek-r1:7b", "hermes-1.5b"]

def ollama_generate(prompt: str, temperature: float = 0.7) -> str:
    """Call local Ollama chat API. Returns generated text or '' on failure."""
    # Try configured model first, then fallback chain
    models_to_try = [MODEL] + [m for m in MODEL_CHAIN if m != MODEL]
    last_error = ""
    for attempt_model in models_to_try:
        payload = {
            "model": attempt_model,
            "messages": [
                {"role": "system", "content": (
                    "You are an expert SEO content writer. Write clear, helpful, "
                    "original articles for beginner readers. Use short paragraphs, "
                    "headings, and a friendly tone. No fluff, no repetition."
                )},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "stream": False,
            "options": {"num_predict": 900},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=420) as resp:
                out = json.loads(resp.read().decode("utf-8"))
            return out.get("message", {}).get("content", "").strip()
        except urllib.error.URLError as e:
            log(f"Ollama error with {attempt_model}: {e}")
            last_error = str(e)
            continue  # try next model in chain
        except Exception as e:
            log(f"Ollama unexpected error with {attempt_model}: {e}")
            last_error = str(e)
            continue
        log(f"All Ollama models failed. Last error: {last_error}")
        return ""


AUTO_TAG_KEYWORDS = {
    "invest": ["nivesh", "invest", "fund", "stock", "market", "stock market", "nivesh kare", "nivesh kar"],
    "savings": ["bachat", "save", "savings", "bachana", "save money", "bank", "fd", "fixed deposit", "account"],
    "credit": ["credit", "kaard", "card", "cibil", "cicil", "loan", "loan"],
    "tax": ["tax", "ttaiks", "80c", "tds", "itr", "income tax", "kaash"],
    "insurance": ["bima", "insurance", "health", "term", "health insurance"],
    "retirement": ["retirement", "nps", "ppf", "retire", "pension", "khaataa"],
    "business": ["business", "side income", "freelance", "freelancing", "gst", "jaayv kaari"],
    "crypto": ["kripto", "bitcoin", "crypto", "blockchain"],
    "realestate": ["real estate", "property", "rent", "ghar", "bhumi", "zameen"],
    "budget": ["budget", "budgeting", "aip", "aips", "kharch", "spend", "manage"],
}

def auto_tags(text: str) -> list:
    text_lower = text.lower()
    tags = []
    for tag, keywords in AUTO_TAG_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            tags.append(tag)
    return tags[:5]

def fallback_article(topic: str) -> str:
    """Used if Ollama is unavailable/slow so the engine never dies."""
    if ENGINE_LANG == "hindi":
        return f"""# {topic}

यह मनी-मेकर इंजन द्वारा तैयार किया गया शुरुआती लेख है: **{topic}**।

## यह क्यों ज़रूरी है
बहुत से लोग रोज़ "{topic}" सर्च करते हैं। इसके बेसिक्स समझने से आप बेहतर फैसले ले सकते हैं और पैसे बचा सकते हैं।

## शुरुआत कैसे करें
- अपने शहर/राज्य में उपलब्ध विकल्पों की रिसर्च करें।
- दाम, फीचर्स और रिव्यूज़ compare करें।
- छोटे से शुरू करें और सीखते-सीखते बढ़ाएं।

## पैसे बचाने के टिप्स
- भुगतान से पहले फ्री ट्रायल लें।
- हर खर्च का हिसाब रखें।
- जो हो सके automatize करें।

> नोट: यह लेख ऑफलाइन फॉलबैक मोड में तैयार हुआ है। Ollama चालू होने पर पूरा AI-लिखित कंटेंट मिलेगा।

## निष्कर्ष
निरंतरता (consistency) ही असली कमाई लाती है। शुरुआत करें और जारी रखें।
"""
    return f"""# {topic.title()}

This is an auto-generated starter article about **{topic}**.

## Why this matters
Many people search for "{topic}" every day. Understanding the basics helps
you make better decisions and save money.

## Getting started
1. Research the options available in your region.
2. Compare prices, features, and reviews.
3. Start small and scale as you learn.

## Tips to save money
- Use free trials before paying.
- Track every expense.
- Automate what you can.

> Note: This article was generated by the Money-Maker engine in offline
> fallback mode. Connect Ollama for full AI-written content.

## Final thought
Consistency beats intensity. Keep showing up, and results compound.
"""


def hindi_article(topic: str) -> str:
    """Reliable, clean, substantial Hindi finance article (no model needed).

    Topic-aware: detects keywords (SIP, tax, credit card, gold, etc.) and
    injects a relevant real-Hindi section so every post is unique + useful.
    """
    import random
    t = topic.strip()
    tips = [
        "अपनी इनकम और खर्च का हिसाब रखें — बिना हिसाब के बचत नहीं होती।",
        "बचत को सैलरी आने के तुरंत बाद 'पेमेंट' की तरह ट्रीट करें (pay yourself first)।",
        "इमरजेंसी फंड बनाएं — कम से कम 3-6 महीने का खर्च बैंक में तैयार रखें।",
        "हाई-इंटरेस्ट डेब्ट (क्रेडिट कार्ड) को सबसे पहले क्लियर करें।",
        "SIP के ज़रिए छोटी रकम (₹500-₹1000/महीना) से भी लंबे समय में अच्छा फंड बनता है।",
        "बीमा और टैक्स-सेविंग (80C, NPS) का फायदा लें — पैसा बचता है और सुरक्षा भी।",
        "ऑनलाइन खरीदारी से पहले कैशबैक और ऑफर्स चेक करें।",
        "फ्री ऐप्स (इंडियन बज़/वॉलेट/बैंक ऐप) से अपना पैसा ट्रैक करें।",
        "ब्रोकर (Groww/Zerodha) से डीमैट अकाउंट फ्री में खोलें और छोटी शुरुआत करें।",
        "हर महीने की बचत को auto-debit/SIP से इन्वेस्ट करें ताकि डिसिप्लिन बना रहे।",
    ]
    random.seed(hash(t) & 0xffffffff)
    picked = random.sample(tips, 5)

    # Topic-specific deep section
    deep = ""
    tl = t.lower()
    if any(k in tl for k in ["sip", "म्यूचुअल", "निवेश", "invest", "nivesh"]):
        deep = ("## SIP और म्यूचुअल फंड समझें\n"
                "- SIP (Systematic Investment Plan) में हर महीने तय रकम (जैसे ₹500) फंड में लगती है।\n"
                "- लंबे समय (7-10 साल) तक चलाने से 'compounding' का फायदा मिलता है।\n"
                "- शुरुआत के लिए लार्ज-कैप या इंडेक्स फंड सुरक्षित रहते हैं।\n"
                "- Groww, Zerodha, Kuvera जैसे ऐप से ₹0 में डीमैट अकाउंट खुलता है।")
    elif any(k in tl for k in ["टैक्स", "tax", "80c", "बचाने"]):
        deep = ("## टैक्स बचाने के असली तरीके\n"
                "- सेक्शन 80C में PPF, ELSS, LIC प्रीमियम, EPFF़ से ₹1.5 लाख तक की बचत होती है।\n"
                "- NPS (80CCD) से अलग से ₹50,000 और बचते हैं।\n"
                "- होम लोन के इंटरेस्ट पर 24(b) का फायदा लें।\n"
                "- टैक्स-सेविंग को मार्च के आखिरी दिन के बजाय शुरुआत में ही प्लान करें।")
    elif any(k in tl for k in ["क्रेडिट कार्ड", "cashback", "कैशबैक", "credit"]):
        deep = ("## क्रेडिट कार्ड सही इस्तेमाल\n"
                "- केवल उतना खर्च करें जितना चुका सकें — बकाया पर 40%+ ब्याज लगता है।\n"
                "- पूरा बिल हर महीने 'time पर' चुकाएं ताकि ब्याज न लगे।\n"
                "- कैशबैक कार्ड (Amazon Pay, HDFC MoneyBack) से रोज़ के खर्च पर रिवॉर्ड मिलता है।\n"
                "- ऑफर्स/वाउचर ज़रूर चेक करें — साल में ₹5,000-₹10,000 बच सकते हैं।")
    elif any(k in tl for k in ["गोल्ड", "gold", "सोना"]):
        deep = ("## गोल्ड में निवेश\n"
                "- सॉफ्ट गोल्ड / डिजिटल गोल्ड (ऐप्स से) छोटी रकम (₹10) से भी शुरू होता है।\n"
                "- Sovereign Gold Bond (SGB) में ब्याज + टैक्स फ्री रहता है।\n"
                "- फिज़िकल सोने पर मेकिंग चार्ज और GST लगता है — डिजिटल बेहतर।\n"
                "- पोर्टफोलियो का 5-10% ही गोल्ड में रखें।")
    elif any(k in tl for k in ["बजट", "budget", "बचत", "save", "बचाने"]):
        deep = ("## बजट और बचत प्लान\n"
                "- 50/30/20 नियम अपनाएं: 50% ज़रूरत, 30% चाहत, 20% बचत/निवेश।\n"
                "- हर खर्च को 1 सप्ताह बाद रिव्यू करें — पता चलेगा पैसा कहाँ बह रहा है।\n"
                "- SUBSCRIPTION और छोटे खर्च (चाय/स्नैक्स) काटकर महीने ₹1000-₹2000 बच सकते हैं।\n"
                "- बची रकम को तुरंत SIP/बैंक FD में डालें, वरना खर्च हो जाती है।")
    elif any(k in tl for k in ["फ्रीलांस", "freelance", "side", "साइड", "कमाने", "income", "इनकम"]):
        deep = ("## साइड इनकम के तरीके\n"
                "- Upwork, Fiverr, Freelancer पर अपनी स्किल (लिखना, डिज़ाइन, कोडिंग) बेचें।\n"
                "- YouTube / Instagram पर निश फॉलोअर्स बनाकर अफिलिएट/ब्रांड डील लें।\n"
                "- छोटी सर्विस (रिज्यूम बनाना, थर्ड-पार्टी सपोर्ट) से महीने ₹5,000-₹20,000 जोड़ सकते हैं।\n"
                "- साइड इनकम को मुख्य बचत के साथ मिलाकर जल्दी फंड बनाएं।")
    else:
        deep = ("## पैसे बढ़ाने के सिद्धांत\n"
                "- आय बढ़ाने और खर्च घटाने — दोनों पर एक साथ काम करें।\n"
                "- छोटी बचत को इन्वेस्ट करें, सिर्फ बैंक में पड़ा रहने देने से इन्फ्लेशन खा जाता है।\n"
                "- हर लक्ष्य (गाड़ी/घर/बच्चों की पढ़ाई) के लिए अलग SIP बनाएं।\n"
                "- साल में 1 बार पूरे पोर्टफोलियो का रिव्यू ज़रूर करें।")

    steps = [
        f"पहला कदम: '{t}' के लिए अपना लक्ष्य तय करें (जैसे महीने में ₹2000 बचाना)।",
        "दूसरा कदम: सही टूल/ऐप चुनें — भारत में बहुत से फ्री ऑप्शन्स मौजूद हैं।",
        "तीसरा कदम: छोटी रकम से शुरुआत करें, फिर धीरे-धीरे बढ़ाएं।",
        "चौथा कदम: हर महीने रिव्यू करें और गलतियों को ठीक करें।",
    ]
    examples = [
        "उदाहरण: हर महीने ₹2000 की SIP, 12% रिटर्न → 10 साल में करीब ₹4.6 लाख।",
        "उदाहरण: क्रेडिट कार्ड सही इस्तेमाल से सालाना ₹5,000-₹10,000 कैशबैक।",
        "उदाहरण: ₹50,000 की सालाना 80C इन्वेस्टमेंट से टैक्स में ~₹15,000 बचत।",
    ]
    body = f"""# {t}

'{t}' हर भारतीय के पैसों से जुड़ा अहम विषय है। इस हिंदी गाइड में हम सरल भाषा में समझाएंगे कि आप इसे अपने फायदे में कैसे इस्तेमाल कर सकते हैं।

## यह क्यों ज़रूरी है
बहुत से लोग रोज़ "{t}" सर्च करते हैं, लेकिन सही जानकारी के बिना पैसे बर्बाद करते हैं। बेसिक समझ बेहतर फैसले लेने में मदद करती है।

{deep}

## शुरुआत कैसे करें
{chr(10).join('- ' + s for s in steps)}

## असली उदाहरण (₹ में)
{chr(10).join('- ' + e for e in examples)}

## त्वरित टिप्स
{chr(10).join('- ' + x for x in picked)}

## निष्कर्ष
{picked[0]} '{t}' में नियमितता ही असली कमाई लाती है — आज ही छोटी शुरुआत करें और जारी रखें।
"""
    return body


def generate_content(topic: str) -> str:
    """Return raw markdown for an article, per configured content_mode."""
    mode = engine_cfg.get("content_mode", "ollama")
    if ENGINE_LANG == "hindi" and mode == "template":
        return hindi_article(topic)
    if mode == "template":
        return fallback_article(topic)
    # ollama mode (attempt AI, fall back to template on failure)
    raw = ""
    for attempt in range(1, 4):
        raw = ollama_generate(make_prompt(topic))
        words = len(re.findall(r"\w+", raw))
        if words >= int(WORDS * 0.5):
            return raw
        log(f"  attempt {attempt}: only {words} words, retrying...")
    log("Ollama weak/slow — using reliable template content.")
    return hindi_article(topic) if ENGINE_LANG == "hindi" else fallback_article(topic)


def make_prompt(topic: str) -> str:
    if ENGINE_LANG == "hindi":
        return (
            f"'{topic}' पर एक पूरा, मूल, SEO-अनुकूल लेख लिखें (हिंदी में)।\n"
            f"जरूरी नियम:\n"
            f"- कम से कम {WORDS} शब्दों का असली, उपयोगी कंटेंट लिखें।\n"
            f"- टाइटल को हेडिंग के रूप में दोबारा न लिखें। सीधे 2-3 वाक्यों का परिचय शुरू करें।\n"
            f"- सेक्शन हेडिंग के लिए सिर्फ '##' का उपयोग करें (जैसे '## यह क्यों जरूरी है')।\n"
            f"- 4-6 '##' सेक्शन लिखें जिनमें व्यावहारिक सलाह हो (भारतीय उदाहरण, ₹ में)।\n"
            f"- '## त्वरित टिप्स' बुलेट सेक्शन शामिल करें (5+ बुलेट)।\n"
            f"- अंत में '## निष्कर्ष' पैराग्राफ लिखें।\n"
            f"- भाषा: साधारण हिंदी, शुरुआती लोगों के लिए, जर्गन नहीं।\n"
            f"- कोड फेंस, HTML या '#' टाइटल का उपयोग न करें। सिर्फ '##' हेडिंग और '- ' बुलेट।"
        )
    return (
        f"Write a complete, original, SEO-friendly article about '{topic.title()}'.\n"
        f"IMPORTANT RULES:\n"
        f"- Write at least {WORDS} words of real, helpful content.\n"
        f"- Do NOT repeat the title as a heading. Start directly with a 2-3 sentence intro paragraph.\n"
        f"- Use exactly '##' for section headings (e.g. '## Why it matters'). No '#' titles.\n"
        f"- Include 4-6 '##' sections with practical, specific advice.\n"
        f"- Include a bulleted '## Quick tips' section (5+ bullets).\n"
        f"- End with a '## Wrap-up' paragraph.\n"
        f"- Audience: absolute beginners. Tone: friendly, plain English, no jargon.\n"
        f"- No markdown code fences, no HTML. Only plain text with '##' headings and '- ' bullets."
    )


def md_to_html(md: str) -> str:
    """Minimal markdown -> HTML converter (stdlib only)."""
    lines = md.split("\n")
    out, in_list = [], False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for ln in lines:
        s = ln.rstrip()
        if not s.strip():
            close_list()
            continue
        elif s.startswith("## "):
            close_list()
            out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("# "):
            # Template already renders the article title as H1. Drop any H1 the
            # model emits so we never end up with duplicate/extra H1 tags.
            close_list()
            continue
        elif s.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(s[2:])}</li>")
        elif s.startswith("> "):
            close_list()
            out.append(f"<blockquote>{inline(s[2:])}</blockquote>")
        else:
            close_list()
            out.append(f"<p>{inline(s)}</p>")
    close_list()
    return "\n".join(out)


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


# --------------------------------------------------------------------------- #
# Affiliate + ads injection
# --------------------------------------------------------------------------- #
def inject_affiliate(body_html: str, topic: str) -> str:
    """Insert Indian affiliate CTAs + ad slots at sensible points."""
    amazon = affiliate.get("amazon_tag", "")
    hosting = affiliate.get("hosting_url", "")
    tool = affiliate.get("software_tool_url", "")
    mf = affiliate.get("mutual_fund_url", "")
    adsense = affiliate.get("adsense_client", "")
    tg = affiliate.get("telegram_channel", "")
    upi = affiliate.get("upi_id", "")
    upi_name = affiliate.get("upi_name", "")
    adsense = affiliate.get("adsense_client", "")
    # Ad slot HTML (only real if AdSense configured with a real client id)
    ad_html = ""
    if adsense and adsense.startswith("ca-pub-") and "0000000000000000" not in adsense:
        ad_html = (
            '<div class="ad"><ins class="adsbygoogle" style="display:block" '
            f'data-ad-client="{adsense}" '
            f'data-ad-slot="{affiliate.get("adsense_slot","")}" '
            'data-ad-format="auto"></ins></div>'
        )
    else:
        ad_html = '<div class="ad placeholder">[ Ad slot — add AdSense in config.json ]</div>'

    # Indian affiliate CTA box
    cta_bits = []
    if amazon and amazon != "yourname-21":
        cta_bits.append(
            f'<a class="affbtn" href="https://www.amazon.in/?tag={amazon}" '
            f'rel="sponsored nofollow">🛒 Amazon.in से खरीदें</a>'
        )
    if mf and "your-" not in mf:
        cta_bits.append(
            f'<a class="affbtn alt" href="{mf}" rel="sponsored nofollow">'
            f'📈 Groww/Zerodha से निवेश शुरू करें</a>'
        )
    if hosting and "your-affiliate" not in hosting and "yourid" not in hosting:
        cta_bits.append(
            f'<a class="affbtn" href="{hosting}" rel="sponsored nofollow">'
            f'🌐 सस्ती वेब होस्टिंग (शुरुआती)</a>'
        )
    if tool and "your-affiliate" not in tool:
        cta_bits.append(
            f'<a class="affbtn alt" href="{tool}" rel="sponsored nofollow">'
            f'🛠️ बेस्ट टूल आजमाएं</a>'
        )
    cta = ""
    if cta_bits:
        cta = '<div class="cta">' + "".join(cta_bits) + "</div>"

    # Telegram CTA (instant traffic channel)
    tg_box = ""
    if tg:
        tg_box = (
            '<div class="cta tg">'
            f'<a class="affbtn" href="{tg}" rel="nofollow">📢 हमारे Telegram चैनल से जुड़ें (रोज़ मनी टिप्स)</a>'
            "</div>"
        )

    # UPI direct-support CTA (instant, no approval needed)
    upi_box = ""
    if upi:
        upi_link = f"upi://pay?pa={upi}&pn={upi_name}&cu=INR"
        upi_box = (
            '<div class="cta upi">'
            f'<a class="affbtn upi-btn" href="{upi_link}">'
            f'💸 इस लेख को पसंद किया? UPI से सपोर्ट करें ({upi})</a>'
            f'<div class="upi-id">UPI: {upi}</div>'
            "</div>"
        )

    # Insert ad after first <h2>, CTA before conclusion near end
    parts = body_html.split("<h2>", 1)
    if len(parts) == 2:
        body_html = parts[0] + ad_html + "\n<h2>" + parts[1]
    else:
        body_html = ad_html + "\n" + body_html

    # CTA near the end (after the last paragraph block, outside any <p>)
    if cta:
        idx = body_html.rfind("</p>")
        if idx != -1:
            end = idx + len("</p>")
            body_html = body_html[:end] + cta + tg_box + upi_box + body_html[end:]
        else:
            body_html += cta + tg_box + upi_box
    elif tg_box:
        body_html += tg_box + upi_box
    elif upi_box:
        body_html += upi_box
    return body_html


# --------------------------------------------------------------------------- #
# Publishing (static site)
# --------------------------------------------------------------------------- #
PAGE_CSS = """
/* premium-v2 */
.featured{margin:14px 0 22px}
.featured img{width:100%;height:auto;display:block;border-radius:16px;border:1px solid var(--line);box-shadow:0 14px 38px rgba(0,0,0,.5)}
.card{overflow:hidden}
.card .thumb{width:100%;aspect-ratio:1200/630;object-fit:cover;border-radius:12px;border:1px solid var(--line);transition:transform .25s ease}
.card:hover .thumb{transform:scale(1.03)}
.card:hover{box-shadow:0 16px 44px rgba(91,140,255,.2);border-color:var(--acc);transform:translateY(-4px)}
.grid{grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
"""


def ensure_css():
    """Append premium-v2 rules to the live stylesheet once (idempotent)."""
    css_path = ASSETS_DIR / "style.css"
    base = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    if "/* premium-v2 */" not in base:
        css_path.write_text(base + "\n" + PAGE_CSS, encoding="utf-8")
        log("style.css upgraded with premium-v2 rules.")


def fetch_featured_image(topic: str, slug: str) -> str:
    """Download a free Pollinations AI featured image; return web path or ''."""
    import urllib.parse
    out = FEATURED_DIR / f"{slug}.jpg"
    if out.exists() and out.stat().st_size > 5000:
        return f"/assets/featured/{slug}.jpg"
    prompt = urllib.parse.quote(
        f"{topic}, personal finance India, premium modern flat illustration, "
        f"dark navy blue theme, rupee coins, glowing accents, no text"
    )
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=1200&height=630&nologo=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        if len(data) > 5000:
            out.write_bytes(data)
            log(f"Featured image saved: {out.name} ({len(data)//1024} KB)")
            return f"/assets/featured/{slug}.jpg"
    except Exception as e:
        log(f"Featured image failed for {slug}: {e}")
    return ""


def featured_img_html(img: str, title: str) -> str:
    if not img:
        return ""
    return (f'<figure class="featured"><img src="{img}" '
            f'alt="{html.escape(title)}" width="1200" height="630"></figure>')


def card_thumb(slug: str, title: str) -> str:
    if (FEATURED_DIR / f"{slug}.jpg").exists():
        return (f'<img class="thumb" src="/assets/featured/{slug}.jpg" '
                f'alt="{html.escape(title)}" loading="lazy">')
    return ""


def _t(en: str, hi: str) -> str:
    return hi if ENGINE_LANG == "hindi" else en



# Reading time estimate
def reading_time(words: int) -> str:
    minutes = max(1, round(words / 200))
    if minutes < 60:
        return f"{minutes} min read"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m read" if m else f"{h}h read"

def share_buttons(title: str, url: str) -> str:
    hi = ENGINE_LANG == "hindi"
    st = html.escape(title)
    u = html.escape(url)
    wa = f"https://wa.me/?text={st}%20{u}"
    tw = f"https://twitter.com/intent/tweet?text={st}&url={u}"
    return f'''<div class="share-row"><span class="share-label">{_t("Share:", "\u0936\u0947\u092F\u0930 \u0915\u0930\u0947\u0902:")}</span><a class="share-btn wa" href="{wa}" target="_blank" rel="noopener" title="WhatsApp">WhatsApp</a><a class="share-btn tw" href="{tw}" target="_blank" rel="noopener" title="X/Twitter">X</a><a class="share-btn tg" href="https://t.me/share/url?url={u}&text={st}" target="_blank" rel="noopener" title="Telegram">Telegram</a><button class="share-btn cp" onclick="navigator.clipboard.writeText(\'{u}\');this.textContent=\'\u2713 Copied'">Copy</button></div>'''


# --------------------------------------------------------------------------- #
# AI Chat Assistant Widget (Ollama-powered)
# --------------------------------------------------------------------------- #
def chat_widget() -> str:
    hi = ENGINE_LANG == "hindi"
    ph_hi = "Kehshe bhai saans paigham kaare (Ask anything in Hindi/English...)"
    ph_en = "Ask anything about money, investing, finance..."
    placeholder = ph_hi if hi else ph_en
    greeting_hi = "Haai! Main tumhara AI Money Assistant hoon. Koi bhai paigham/nivesh se juda sawaal poocho!"
    greeting_en = "Hi! I am your AI Money Assistant. Ask me anything about money, investing, or finance!"
    greeting = greeting_hi if hi else greeting_en
    _NL = chr(10)
    parts = [
        '<div id="ai-chat" class="chat-widget">',
        '  <button class="chat-toggle" onclick="toggleChat()" title="AI Assistant">&#x1f4ac;</button>',
        '  <div class="chat-box" id="chat-box" style="display:none">',
        '    <div class="chat-header"><h4>&#x1f916; AI Money Assistant</h4><button class="chat-close" onclick="toggleChat()">&#x2715;</button></div>',
        '    <div class="chat-messages" id="chat-messages">',
        '      <div class="chat-msg ai">' + greeting + '</div>',
        '    </div>',
    ]
    if hi:
        parts.append('    <div class="chat-msg ai">Chat mein Hindi mein poocho!</div>')
    parts += [
        '    <div class="chat-input-row">',
        '      <input id="chat-input" type="text" placeholder="' + placeholder + '" onkeydown="if(event.key==\'Enter\')sendChat()">',
        '      <button class="btn primary" onclick="sendChat()">Send</button>',
        '    </div>',
        '  </div>',
        '</div>',
        '<script src="/assets/chat.js"></script>',
    ]
    return _NL.join(parts)

def quiz_widget() -> str:
    hi = ENGINE_LANG == "hindi"
    h_title = "🧠 Paison Ka Quiz" if hi else "🧠 Money Quiz"
    h_sub = "Tumhari financial knowledge test karo" if hi else "Test your financial knowledge"
    return f'''<section class="quiz-section" id="quiz">
  <div class="quiz-header">
    <h2>{h_title}</h2>
    <p>{h_sub}</p>
  </div>
  <div class="quiz-box">
    <div id="quiz-box"></div>
  </div>
</section>
<link rel="stylesheet" href="/assets/quiz.css">
<script src="/assets/quiz.js"></script>
'''

def newsletter_block() -> str:
    hi = ENGINE_LANG == "hindi"
    title = "📬 पैसे के टिप्स ईमेल में पाएं" if hi else "📬 Get money tips in your inbox"
    sub = ("हफ्ते में एक प्रैक्टिकल पैसे/टेक टिप — बिना स्पैम, कभी भी अनसब्सक्राइब करें।"
           if hi else "Join the newsletter. One practical money/tech tip per week — no spam, unsubscribe anytime.")
    btn = "फ्री सब्सक्राइब करें" if hi else "Subscribe free"
    note = ("हम आपके इनबॉक्स का सम्मान करते हैं। कभी-कभार अपडेट के लिए सहमति दें।"
            if hi else "We respect your inbox. By subscribing you agree to receive occasional updates.")
    return f'''
<section class="news">
  <h3>{title}</h3>
  <p>{sub}</p>
  <form action="mailto:bhaveshkumawat632@gmail.com?subject=Newsletter%20Subscribe" method="POST" enctype="text/plain" onsubmit="return trackLead(event)">
    <input type="email" name="email" placeholder="you@example.com" required>
    <button type="submit">{btn}</button>
  </form>
  <div class="note">{note}</div>
</section>'''


def tools_block() -> str:
    hi = ENGINE_LANG == "hindi"
    cur = CURRENCY
    h = "🧮 फ्री बचत कैलकुलेटर" if hi else "🧮 Free Savings Calculator"
    l1 = f"महीने की बचत ({cur})" if hi else f"Monthly savings ({cur})"
    l2 = "साल" if hi else "Years"
    l3 = "सालाना रिटर्न (%)" if hi else "Expected annual return (%)"
    b = "कैलकुलेट करें" if hi else "Calculate"
    r0 = "फील्ड भरें और कैलकुलेट दबाएं।" if hi else "Fill the fields and hit Calculate."
    r1 = f"कुछ साल बाद आपके पास ≈ {{AMT}} ({cur}) हो सकते हैं।" if hi else f"In {{AMT}} years you could have ≈ {{AMT}} ({cur})."
    return f'''
<section class="tool" id="savings-calc">
  <h3>{h}</h3>
  <label>{l1}</label>
  <input id="sc-monthly" type="number" value="2000" min="0">
  <label>{l2}</label>
  <input id="sc-years" type="number" value="5" min="1" max="50">
  <label>{l3}</label>
  <input id="sc-rate" type="number" value="8" min="0" max="30">
  <button class="btn primary" style="margin-top:12px" onclick="calcSavings()">{b}</button>
  <div class="result" id="sc-result">{r0}</div>
</section>
<script src="/assets/tools.js"></script></script>'''


def jsonld_article(title: str, url: str, desc: str, keywords: str = "") -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "keywords": keywords,
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "mainEntityOfPage": url,
    }
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def render_page(title: str, body_html: str, is_post: bool = False,
                desc: str = "", url: str = "", image: str = "") -> str:
    adsense = affiliate.get("adsense_client", "")
    ads_script = (
        '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>'
        if adsense.startswith("ca-pub-") and "0000000000000000" not in adsense else ""
    )
    # Google AdSense site-ownership verification meta tag (added for account approval)
    adsense_verify = (
        '<meta name="google-adsense-account" content="ca-pub-3041951952998611">'
        if adsense.startswith("ca-pub-") and "0000000000000000" not in adsense else
        '<meta name="google-adsense-account" content="ca-pub-3041951952998611">'
    )
    jsonld = jsonld_article(title, url, desc, keywords=KEYWORDS) if is_post else ""
    breadcrumb_ld = (
        f'<script type="application/ld+json">{{"@context":"https://schema.org",'
        f'"@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem",'
        f'"position":1,"name":"Home","item":"{DOMAIN}/"}},{{"@type":"ListItem",'
        f'"position":2,"name":"{html.escape(title)}","item":"{html.escape(url or DOMAIN)}"}}]}}</script>'
    ) if is_post else ""
    og = (
        f'<meta property="og:title" content="{html.escape(title)}">'
        f'<meta property="og:description" content="{html.escape(desc or title)}">'
        f'<meta property="og:type" content="{"article" if is_post else "website"}">'
        f'<meta property="og:url" content="{html.escape(url or DOMAIN)}">'
    )
    if image:
        img_url = html.escape(DOMAIN + image)
        og += (
            f'<meta property="og:image" content="{img_url}">'
            f'<meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:image" content="{img_url}">'
        )
    return f"""<!DOCTYPE html>
<html lang="{LANG}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | {html.escape(SITE_NAME)}</title>
<meta name="description" content="{html.escape(desc or title)} — by {html.escape(SITE_NAME)}.">
<link rel="canonical" href="{html.escape(url or DOMAIN)}">
<meta name="keywords" content="{html.escape(KEYWORDS)}">
<meta name="robots" content="index, follow, max-image-preview:large">
{og}
<link rel="stylesheet" href="/assets/style.css">
<link rel="alternate" type="application/rss+xml" title="{html.escape(SITE_NAME)}" href="/feed.xml">
{ads_script}
{adsense_verify}
{jsonld}
{breadcrumb_ld}
</head>
<body>
<button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌙</button>
<script src="/assets/theme.js"></script>
<header class="site">
  <nav class="nav">
    <div class="brand"><span class="dot"></span>{html.escape(SITE_NAME)}</div>
    <div class="links">
      <a href="/">{_t("Home", "होम")}</a>
      <a href="/#guides">{_t("Guides", "गाइड्स")}</a>
      <a href="/#tools">{_t("Tools", "टूल्स")}</a>
      <a href="/#news">{_t("Newsletter", "न्यूज़लेटर")}</a>
    </div>
    <input id="site-search" class="nav-search" type="search" placeholder="{_t('Search…', 'खोजें…')}" onkeyup="filterCards(this.value)">
  </nav>
</header>
{body_html}
<footer class="site">
  © {datetime.datetime.now().year} {html.escape(SITE_NAME)} · {_t("Built & auto-published by Money-Maker Engine", "Money-Maker Engine द्वारा ऑटो-पब्लिश")} ·
  <a href="/sitemap.xml">Sitemap</a> ·
  <a href="/privacy.html">{_t("Privacy", "प्राइवेसी")}</a> ·
  <a href="/disclaimer.html">{_t("Disclaimer", "डिस्क्लेमर")}</a> ·
  <a href="/about.html">{_t("About", "अबाउट")}</a> ·
  <a href="/contact.html">{_t("Contact", "संपर्क")}</a> ·
  <a href="/dashboard.html">{_t("Dashboard", "डैशबोर्ड")}</a>
</footer>
<img class="tracker" src="/t.gif?p={html.escape(slugify(title))}" width="1" height="1" alt="">
</body>
</html>"""


def write_index(posts_meta: list):
    cards = []
    for p in sorted(posts_meta, key=lambda x: x["ts"], reverse=True):
        cat = p.get("category", "guide")
        cards.append(
            f'<a class="card" data-cat="{html.escape(cat)}" href="/posts/{p["slug"]}.html">'
            + card_thumb(p["slug"], p["title"])
            + f'<span class="tag">{html.escape(cat.title())}</span>'
            f'<h3>{html.escape(p["title"])}</h3>'
            f'<div class="meta">📅 {p["date"]} · ⏱ {p["words"]} {_t("words", "शब्द")}</div></a>'
        )
    card_grid = '<div class="grid" id="card-grid">' + "".join(cards) + "</div>"
    hero_btn1 = _t("📖 Read Guides", "📖 गाइड्स पढ़ें")
    hero_btn2 = _t("🧮 Try Free Tools", "🧮 फ्री टूल्स आजमाएं")
    guides_h = _t("Latest Guides", "ताज़ा गाइड्स")
    guides_s = _t("Fresh, AI-written, money-focused", "ताज़ा, AI-लिखित, पैसे वाले")
    body = f'''
<section class="hero">
  <h1>{html.escape(SITE_NAME)}</h1>
  <p>{html.escape(TAGLINE)}</p>
  <div class="cta-row">
    <a class="btn primary" href="#guides">{hero_btn1}</a>
    <a class="btn ghost" href="#tools">{hero_btn2}</a>
    <a class="btn primary" href="#quiz" style="background:linear-gradient(135deg,#22d3a8,#5b8cff)">🧠 Quiz Try Karo</a>
  </div>
</section>
<section class="wrap" id="guides">
  <div class="section-title"><h2>{guides_h}</h2><span class="sub">{guides_s}</span></div>
  <div class="chip-row" id="cat-chips">
    <button class="chip active" onclick="setCat('all',this)">सभी</button>
    <button class="chip" onclick="setCat('invest',this)">निवेश</button>
    <button class="chip" onclick="setCat('save',this)">बचत</button>
    <button class="chip" onclick="setCat('credit',this)">क्रेडिट</button>
    <button class="chip" onclick="setCat('tax',this)">टैक्स</button>
    <button class="chip" onclick="setCat('guide',this)">गाइड</button>
  </div>
  {card_grid}
</section>
<section class="wrap" id="tools">{tools_block()}</section>
<section class="wrap" id="quiz">{quiz_widget()}</section>
<section class="wrap" id="news">{newsletter_block()}</section>
<script src="/assets/filter.js"></script>'''
    (SITE_DIR / "index.html").write_text(
        render_page("Home", body, desc=TAGLINE, url=DOMAIN + "/"), encoding="utf-8"
    )


def write_feed(posts_meta: list):
    items = []
    for p in sorted(posts_meta, key=lambda x: x["ts"], reverse=True)[:20]:
        link = f"{DOMAIN}/posts/{p['slug']}.html"
        items.append(
            f"  <item><title>{html.escape(p['title'])}</title>"
            f"<link>{html.escape(link)}</link>"
            f"<guid>{html.escape(link)}</guid>"
            f"<pubDate>{datetime.datetime.utcfromtimestamp(p['ts']).strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>"
            f"<description>{html.escape(p['title'])} — practical guide.</description></item>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
        f"  <title>{html.escape(SITE_NAME)}</title>\n"
        f"  <link>{html.escape(DOMAIN)}</link>\n"
        f"  <description>{html.escape(TAGLINE)}</description>\n"
        + "\n".join(items)
        + "\n</channel>\n</rss>\n"
    )
    (SITE_DIR / "feed.xml").write_text(xml, encoding="utf-8")


def write_sitemap(posts_meta: list):
    urls = [f"{DOMAIN}/", f"{DOMAIN}/index.html", f"{DOMAIN}/feed.xml"]
    for p in posts_meta:
        urls.append(f"{DOMAIN}/posts/{p['slug']}.html")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url><loc>{html.escape(u)}</loc></url>\n"
    xml += "</urlset>\n"
    (SITE_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_robots():
    (SITE_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8"
    )


def _legal_page(title: str, body: str) -> str:
    return render_page(
        title,
        f'<article class="post"><div class="breadcrumb"><a href="/">'
        f'{_t("Home", "होम")}</a> / {html.escape(title)}</div>'
        f'<h1>{html.escape(title)}</h1>{body}</article>',
        True, desc=title, url=f"{DOMAIN}/{slugify(title)}.html",
    )


def write_static_pages():
    """Generate AdSense-required legal pages + an earnings dashboard."""
    hi = ENGINE_LANG == "hindi"

    # Privacy Policy
    privacy = (
        "<p>" + (_t(
            "We respect your privacy. This site uses Google AdSense to serve ads. "
            "AdSense and its partners may use cookies to serve ads based on your "
            "prior visits. You can opt out of personalised advertising by visiting "
            "Ads Settings. We do not sell your personal data.",
            "हम आपकी प्राइवेसी का सम्मान करते हैं। यह साइट Google AdSense का उपयोग विज्ञापन दिखाने के लिए करती है। "
            "AdSense और उसके पार्टनर्स कुकीज़ का उपयोग आपकी पिछली विज़िट्स के आधार पर ऐड्स दिखाने में कर सकते हैं। "
            "आप Ads Settings जाकर पर्सनलाइज़्ड एडवरटाइज़िंग बंद कर सकते हैं। हम आपका पर्सनल डेटा नहीं बेचते।"
        )) + "</p>"
        "<h2>" + _t("Cookies", "कुकीज़") + "</h2><p>" + _t(
            "Third-party vendors may use cookies for advertising. Learn more at "
            "Google's Advertising Policies.",
            "थर्ड-पार्टी वेंडर्स विज्ञापन के लिए कुकीज़ इस्तेमाल कर सकते हैं। अधिक जानकारी Google Advertising Policies पर।"
        ) + "</p>"
        "<h2>" + _t("Contact", "संपर्क") + "</h2><p>" + _t(
            "Questions? Email us at privacy@example.com.",
            "सवाल हैं? हमें privacy@example.com पर ईमेल करें।"
        ) + "</p>"
    )
    (SITE_DIR / "privacy.html").write_text(_legal_page(_t("Privacy Policy", "प्राइवेसी पॉलिसी"), privacy), encoding="utf-8")

    # Disclaimer
    disclaimer = (
        "<p>" + _t(
            "The content on this site is for educational purposes only and is not "
            "financial advice. We may earn a commission from affiliate links at no "
            "extra cost to you. Always do your own research before investing or buying.",
            "इस साइट का कंटेंट सिर्फ एजुकेशनल है और फाइनेंशियल एडवाइस नहीं है। हम affiliate लिंक्स से कमीशन कमा सकते हैं, "
            "आपको एक्स्ट्रा चार्ज नहीं लगता। निवेश या खरीदारी से पहले हमेशा खुद रिसर्च करें।"
        ) + "</p>"
        "<h2>" + _t("Affiliate disclosure", "अफिलिएट डिस्क्लोज़र") + "</h2><p>" + _t(
            "Some links are affiliate links. If you buy via them we may earn a commission.",
            "कुछ लिंक्स अफिलिएट हैं। अगर आप उनसे खरीदते हैं तो हमें कमीशन मिल सकता है।"
        ) + "</p>"
    )
    (SITE_DIR / "disclaimer.html").write_text(_legal_page(_t("Disclaimer", "डिस्क्लेमर"), disclaimer), encoding="utf-8")

    # About
    about = (
        "<p>" + _t(
            f"{SITE_NAME} is an automated money & tech guide. Articles are written by a "
            "local AI engine and published 24/7 to help beginners save, earn and grow.",
            f"{SITE_NAME} एक ऑटोमेटेड पैसे और टेक गाइड है। लेख एक लोकल AI इंजन द्वारा लिखे जाते हैं और 24/7 "
            "शुरुआती लोगों को बचाने, कमाने और बढ़ने में मदद करने के लिए पब्लिश होते हैं।"
        ) + "</p>"
        "<h2>" + _t("Our mission", "हमारा मिशन") + "</h2><p>" + _t(
            "Make practical money knowledge free and accessible to everyone in India.",
            "भारत के हर व्यक्ति तक प्रैक्टिकल पैसे की जानकारी फ्री और आसान बनाना।"
        ) + "</p>"
    )
    (SITE_DIR / "about.html").write_text(_legal_page(_t("About Us", "हमारे बारे में"), about), encoding="utf-8")

    # Contact
    contact = (
        "<p>" + _t(
            "We'd love to hear from you. Email: contact@example.com",
            "आपकी बात सुनना चाहेंगे। ईमेल: contact@example.com"
        ) + "</p>"
        "<h2>" + _t("Business enquiries", "बिज़नेस इनक्वायरी") + "</h2><p>" + _t(
            "For affiliate or advertising partnerships, reach out via email.",
            "अफिलिएट या एडवरटाइज़िंग पार्टनरशिप के लिए ईमेल करें।"
        ) + "</p>"
    )
    (SITE_DIR / "contact.html").write_text(_legal_page(_t("Contact Us", "संपर्क करें"), contact), encoding="utf-8")

    # Earnings dashboard (live stats)
    dash = (
        "<p>" + _t("Live performance of this automated engine:",
                   "इस ऑटोमेटेड इंजन का लाइव परफॉर्मेंस:") + "</p>"
        "<div class='grid'>"
        "<div class='card'><h3>" + _t("Articles published", "पब्लिश लेख") + "</h3>"
        "<div class='meta' id='d-gen'>—</div></div>"
        "<div class='card'><h3>" + _t("Page views", "पेज व्यूज़") + "</h3>"
        "<div class='meta' id='d-imp'>—</div></div>"
        "<div class='card'><h3>" + _t("Leads captured", "लीड्स") + "</h3>"
        "<div class='meta' id='d-lead'>—</div></div>"
        "<div class='card'><h3>" + _t("Est. earnings", "अनुमानित कमाई") + "</h3>"
        "<div class='meta' id='d-earn'>—</div></div>"
        "</div>"
        "<script>"
        "fetch('/stats.json').then(r=>r.json()).then(s=>{"
        "document.getElementById('d-gen').textContent=s.generated||0;"
        "document.getElementById('d-imp').textContent=s.impressions||0;"
        "document.getElementById('d-lead').textContent=s.leads||0;"
        "document.getElementById('d-earn').textContent='₹ '+(s.earnings_estimate||0).toFixed(2);"
        "});</script>"
    )
    (SITE_DIR / "dashboard.html").write_text(_legal_page(_t("Live Dashboard", "लाइव डैशबोर्ड"), dash), encoding="utf-8")

    # Add legal/utility links to footer via a small nav page list (footer already has sitemap)
    log("Wrote static pages: privacy, disclaimer, about, contact, dashboard.")


def related_posts_html(posts_meta: list, current_slug: str, n: int = 3) -> str:
    others = [p for p in sorted(posts_meta, key=lambda x: x["ts"], reverse=True)
              if p["slug"] != current_slug][:n]
    if not others:
        return ""
    hi = ENGINE_LANG == "hindi"
    items = "".join(
        f'<a class="card" href="/posts/{p["slug"]}.html">'
        + card_thumb(p["slug"], p["title"]) +
        f'<span class="tag">Guide</span><h3>{html.escape(p["title"])}</h3></a>'
        for p in others
    )
    return (
        f'<section class="wrap"><div class="section-title"><h2>'
        f'{_t("Related guides", "रिलेटेड गाइड्स")}</h2></div>'
        f'<div class="grid">{items}</div></section>'
    )


def update_stats():
    stats = {"generated": 0, "impressions": 0, "clicks": 0, "leads": 0, "earnings_estimate": 0.0}
    if STATS_PATH.exists():
        stats.update(json.loads(STATS_PATH.read_text(encoding="utf-8")))
    return stats


# --------------------------------------------------------------------------- #
# Tiny tracker server (impressions/clicks) — stdlib http.server
# --------------------------------------------------------------------------- #
def run_tracker(host="0.0.0.0", port=8800):
    import http.server
    import socketserver
    from http.server import SimpleHTTPRequestHandler

    stats = update_stats()
    data = load_json(POSTS_DB, [])

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(SITE_DIR), **k)


        def send_json(self, data):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        def do_GET(self):
            if self.path.startswith("/t.gif"):
                from urllib.parse import urlparse, parse_qs
                q = parse_qs(urlparse(self.path).query)
                stats["impressions"] = stats.get("impressions", 0) + 1
                if q.get("e", [""])[0] == "lead":
                    stats["leads"] = stats.get("leads", 0) + 1
                save_json(STATS_PATH, stats)
                # 1x1 transparent gif
                gif = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
                self.send_response(200)
                self.send_header("Content-Type", "image/gif")
                self.send_header("Content-Length", str(len(gif)))
                self.end_headers()
                self.wfile.write(gif)
                return
            if self.path.startswith("/stats.json"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                # Serve latest persisted stats (engine updates the file).
                self.wfile.write(json.dumps(update_stats()).encode())
                return
            super().do_GET()


        def do_POST(self):
            if self.path == "/api/chat":
                try:
                    cl = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(cl)) if cl else {}
                    msg = body.get("message", "")
                    if not msg:
                        self.send_json({"reply": ""})
                        return
                    # Build context: last 6 messages
                    ctx = body.get("context", [])
                    hist = "\n".join(
                        f"{m.get('role','user').capitalize()}: {m.get('content','')}"
                        for m in ctx[-6:]
                    )
                    prompt = f"{hist}\nUser: {msg}\nAssistant:"
                    try:
                        reply = ollama_generate(prompt, temperature=0.3)
                        if not reply.strip():
                            reply = "समस्या आ रही है। कृपया दोबारा कोशिश करें।" if ENGINE_LANG == "hindi" else "Sorry, something went wrong. Please try again."
                    except Exception as e:
                        log(f"ollama chat error: {e}")
                        reply = "AI assistant offline."
                    self.send_json({"reply": reply[:800]})
                except Exception as e:
                    log(f"chat error: {e}")
                    self.send_json({"reply": "Error."})
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, *a):
            pass  # quiet

    with socketserver.TCPServer((host, port), Handler) as httpd:
        log(f"Tracker server running at http://{host}:{port}")
        httpd.serve_forever()


# --------------------------------------------------------------------------- #
# Main cycle
# --------------------------------------------------------------------------- #
def next_topic() -> str:
    done = {p["title"].lower() for p in load_json(POSTS_DB, [])}
    pending = [t for t in topics if t.lower() not in done]
    if not pending:  # cycle again if we exhausted the list
        return random.choice(topics)
    return random.choice(pending)


def publish_post():
    topic = next_topic()
    slug = slugify(topic)
    log(f"Generating article: {topic}")

    raw = generate_content(topic)
    q = quality_score(raw) if raw else {"score": 0, "issues": ["empty"], "readability": {}}
    log(f"  quality score: {q.get('score', 0)}/100, issues: {q.get('issues', [])}")
    if not raw or len(raw) < 120:
        log("Content generation empty — using fallback.")
        raw = fallback_article(topic)

    body = md_to_html(raw)
    body = inject_affiliate(body, topic)

    ts = time.time()
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    words = len(re.findall(r"\w+", raw))

    # Load existing posts BEFORE rendering so related-posts can be computed.
    posts = load_json(POSTS_DB, [])
    posts = [p for p in posts if p["slug"] != slug]  # drop any stale duplicate

    img = fetch_featured_image(topic, slug)
    page = render_page(
        topic,
        f'<article class="post"><div class="breadcrumb"><a href="/">'
        f'{_t("Home", "होम")}</a> / {html.escape(topic.title())}</div>'
        f'<h1>{html.escape(topic.title())}</h1>{featured_img_html(img, topic)}{body}</article>'
        + related_posts_html(posts, slug),
        True,
        desc=topic.title(),
        url=f"{DOMAIN}/posts/{slug}.html",
        image=img,
    )
    (POSTS_DIR / f"{slug}.html").write_text(page, encoding="utf-8")

    posts.append({"title": topic, "slug": slug, "ts": ts, "date": date, "words": words, "quality": q.get("score", 0), "tags": tags if 'tags' in dir() else []})
    if len(posts) > MAX_POSTS:
        posts = posts[-MAX_POSTS:]
    save_json(POSTS_DB, posts)

    write_index(posts)
    write_feed(posts)
    write_sitemap(posts)
    write_robots()
    write_static_pages()

    stats = update_stats()
    stats["generated"] = stats.get("generated", 0) + 1
    save_json(STATS_PATH, stats)

    # Auto-distribution draft (Telegram) — queued for one-click forward
    try:
        tg = affiliate.get("telegram_channel", "")
        public_url = f"{DOMAIN}/posts/{slug}.html"
        share = f"📢 नया लेख: {topic}\n{public_url}\n{tg}\n"
        with open("data/telegram_queue.txt", "a", encoding="utf-8") as q:
            q.write(share + "---\n")
    except Exception as e:
        log(f"Telegram queue write failed: {e}")

    log(f"Published: posts/{slug}.html  ({words} words)  total={stats['generated']}")
    return slug


def rebuild_site():
    """Re-render index/feed/sitemap from existing posts.json (no new articles)."""
    posts = load_json(POSTS_DB, [])
    ensure_css()
    for p in posts:
        slug = p["slug"]
        fpath = POSTS_DIR / f"{slug}.html"
        if not fpath.exists():
            continue
        html_text = fpath.read_text(encoding="utf-8")
        m = re.search(r"<article[^>]*>(.*)</article>", html_text, re.S)
        body = m.group(1) if m else ""
        # Strip any stray H1 / old featured image (re-injected fresh below).
        body = re.sub(r"<h1>.*?</h1>", "", body, flags=re.S)
        body = re.sub(r'<figure class="featured">.*?</figure>', "", body, flags=re.S)
        # Re-inject fresh affiliate CTAs (so config changes like amazon_tag apply on rebuild)
        body = inject_affiliate(body, p["title"])
        img = fetch_featured_image(p["title"], slug)
        page = render_page(
            p["title"],
            f'<article class="post"><div class="breadcrumb"><a href="/">Home</a> / {html.escape(p["title"].title())}</div>'
            f'<h1>{html.escape(p["title"].title())}</h1>{featured_img_html(img, p["title"])}{body}</article>'
            + related_posts_html(posts, slug),
            True, desc=p["title"], url=f"{DOMAIN}/posts/{slug}.html",
            image=img,
        )
        fpath.write_text(page, encoding="utf-8")
    write_index(posts)
    write_feed(posts)
    write_sitemap(posts)
    write_robots()
    write_static_pages()
    log(f"Rebuilt site with {len(posts)} posts (new template).")


def run_once():
    try:
        publish_post()
    except Exception as e:
        log(f"ERROR in cycle: {e}")


def run_loop():
    log("Money-Maker Engine started (loop mode).")
    run_once()  # publish immediately
    while True:
        log(f"Sleeping {RUN_EVERY} min until next article...")
        time.sleep(RUN_EVERY * 60)
        run_once()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "tracker":
        run_tracker()
    elif len(sys.argv) > 1 and sys.argv[1] == "once":
        run_once()
        print("DONE")
    elif len(sys.argv) > 1 and sys.argv[1] == "rebuild":
        rebuild_site()
        print("REBUILT")
    else:
        run_loop()
