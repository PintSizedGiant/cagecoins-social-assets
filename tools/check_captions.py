#!/usr/bin/env python3
"""Check drafted captions against the manifest before anything is written to Airtable.

  python3 tools/check_captions.py build/manifest.json captions.json

captions.json: [{"key": "<manifest key>", "platform": "Instagram"|"X", "caption": "...", "hashtags": "#UFC #MMA", "mentions": "@handle"}]
Fails (exit 1) when a caption contains a number that is not in that post's facts or alt text,
when an X post is over 280 characters, when a ticker is written with a $ in front, or when a banned word is used."""
import json, re, sys
BANNED = ["bet", "bets", "betting", "odds", "wager", "gamble", "gambling", "winnings", "invest", "investment", "guaranteed", "profit",
          "delve", "unleash", "unlock", "elevate", "game-changer", "seamlessly", "robust", "pivotal", "testament", "tapestry", "embark", "journey"]
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
def nums(s): return {n.replace(",", "").rstrip(".") for n in NUM.findall(s)}
def norm(n):
    try: return f"{float(n):g}"
    except ValueError: return n
m = {p["key"]: p for p in json.load(open(sys.argv[1]))["posts"]}
bad = 0
for c in json.load(open(sys.argv[2])):
    p = m.get(c["key"]); probs = []
    if not p: probs.append("key not in manifest")
    else:
        allowed = {norm(n) for n in nums(" ".join(p["facts"]) + " " + p["alt_text"] + " " + p["title"] + " 2000")}
        extra = sorted(n for n in nums(c["caption"]) if norm(n) not in allowed)
        if extra: probs.append("numbers not in the facts: " + ", ".join(extra))
        if c["platform"] not in p["platforms"]: probs.append(f"platform {c['platform']} not planned for this post")
    full = " ".join(x for x in [c["caption"], c.get("hashtags", ""), c.get("mentions", "")] if x)
    if c["platform"] == "X" and len(full) > 280: probs.append(f"X post is {len(full)} characters (limit 280)")
    if re.search(r"\$[A-Za-z]", full): probs.append("ticker written with a $ in front")
    if "—" in full or "–" in full: probs.append("contains a long dash")
    words = set(re.findall(r"[a-z\-]+", full.lower()))
    hit = [b for b in BANNED if b in words]
    if hit: probs.append("banned words: " + ", ".join(hit))
    n_tags = len(re.findall(r"#\w+", full))
    if c["platform"] == "Instagram" and not 3 <= n_tags <= 5: probs.append(f"Instagram needs 3 to 5 hashtags, found {n_tags}")
    if c["platform"] == "X" and n_tags > 2: probs.append(f"X allows at most 2 hashtags, found {n_tags}")
    print(("FAIL " if probs else "ok   ") + c["key"] + " | " + c["platform"] + ("" if not probs else "\n     - " + "\n     - ".join(probs)))
    bad += bool(probs)
sys.exit(1 if bad else 0)
