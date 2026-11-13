#!/usr/bin/env python3
"""Cage Coins social planner (daily plan agreed with Oli, 13/11/2026).

  python3 tools/plan.py raw.json --today YYYY-MM-DD --out build [--photos-ok GANE,HOKI] [--log log/posted.jsonl] [--snapshots snapshots]

Decides which posts this run makes, renders them, gives each one a slot, and writes build/manifest.json.
Captions are written afterwards from each post's facts; nothing here writes captions.

Run days and what they cover (Europe/Paris):
  Sunday    -> Sunday, Monday, Tuesday.        Half 1 (last event review) when the last event was in the past 4 days.
  Wednesday -> Wednesday to Saturday.          Half 2 (next event preview) when the next event is in the next 4 days.
  1st of the month (any weekday) -> also the monthly posts (T6 trader of the month, T12 monthly leaderboard).
  Any other day -> only the monthly posts if it is the 1st, otherwise nothing (Friday is a send-only day).
Slots per day: event week   Instagram 18:30, X 12:30 and 20:30.
               no event     Instagram 18:30, X 18:30.
               monthly      Instagram 15:30, X 15:30 on the 1st (extra, on top of the day's slots).
Posts already in the log are never made again. A filler T7 for a fighter is not repeated within 14 days on a platform."""
import argparse, datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_render as R
import cc_fighter as F
import cc_finish as FIN
import cc_h2h as HH
import cc_extra as X
import cc_fallback as FB
from build import load, dmy, method_h, moved, num, pc, mv, t7_rec, t7_facts

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIG_MOVE = 25.0        # % event move that makes a fighter a "big mover"
FAIR_GAP = 20.0        # % gap between traded price and fair price worth a mention
COOLDOWN_DAYS = 14
SLOTS_EVENT = {"Instagram": ["18:30"], "X": ["12:30", "20:30"]}
SLOTS_QUIET = {"Instagram": ["18:30"], "X": ["18:30"]}
MONTHLY_SLOT = "15:30"
AI_FLAG = ("Contains an AI-generated image of a real fighter. Buffer's 'AI-generated' setting must be on. "
           "Likeness rights in advertising are a question for a lawyer.")

def ddate(s): return dt.date.fromisoformat(str(s)[:10])
def event_tag(ev):
    n = ev["name"]
    if n.upper().startswith("UFC FIGHT NIGHT"): return "#UFCFightNight"
    head = n.split(":")[0].replace(" ", "")
    return "#" + head if head[3:].isdigit() else "#UFC"
def name_tag(name): return "#" + "".join(ch for ch in name.title() if ch.isalnum())
def short(ev): return ("FIGHT NIGHT" if ev["name"].upper().startswith("UFC FIGHT NIGHT") else ev["name"].split(":")[0].upper()) + " · " + dmy(ev["date"])

def blocked():
    p = os.path.join(REPO, "config", "blocked_usernames.txt")
    if not os.path.exists(p): return set()
    return {l.strip().lower() for l in open(p, encoding="utf-8") if l.strip() and not l.startswith("#")}
def mask(u, bl): return "***" if (u or "").lower() in bl else u

def read_log(path):
    out = []
    if path and os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            l = l.strip()
            if l: out.append(json.loads(l))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw"); ap.add_argument("--today", required=True); ap.add_argument("--out", default="build")
    ap.add_argument("--photos-ok", default=""); ap.add_argument("--log", default=os.path.join(REPO, "log", "posted.jsonl"))
    ap.add_argument("--snapshots", default=os.path.join(REPO, "snapshots"))
    a = ap.parse_args()
    d = load(a.raw); today = ddate(a.today); ok = {t.strip().upper() for t in a.photos_ok.split(",") if t.strip()}
    prof = d.get("profiles") or {}; bl = blocked(); log = read_log(a.log)
    done_keys = {(e["key"], e["platform"]) for e in log}
    posts, notes = [], []
    last, nxt = d.get("last"), d.get("next")
    for ev in (last, nxt):
        for b in (ev or {}).get("bouts") or []:
            num(b["red"], "price", "old", "new"); num(b["blue"], "price", "old", "new")

    # ---------------------------------------------------------------- snapshot (kept for the monthly post on the 1st)
    os.makedirs(a.snapshots, exist_ok=True)
    json.dump(dict(generated_at=d.get("generated_at"), leaderboard=d.get("leaderboard"), leaderboard_monthly=d.get("leaderboard_monthly")),
              open(os.path.join(a.snapshots, f"{today.isoformat()}.json"), "w"), indent=1, ensure_ascii=False)

    # ---------------------------------------------------------------- which days and which half
    wd = today.weekday()   # Mon 0 .. Sun 6
    days = []
    if wd == 6: days = [today + dt.timedelta(i) for i in range(3)]
    elif wd == 2: days = [today + dt.timedelta(i) for i in range(4)]
    half1 = wd == 6 and last and 0 <= (today - ddate(last["date"])).days <= 4
    half2 = wd == 2 and nxt and 0 <= (ddate(nxt["date"]) - today).days <= 4
    monthly = today.day == 1
    slots_by_day = SLOTS_EVENT if (half1 or half2) else SLOTS_QUIET

    # ---------------------------------------------------------------- helpers to make posts
    def photo(ticker):
        if ticker and ticker in ok:
            for ext in ("png", "webp", "avif"):
                p = os.path.join(REPO, "photos", f"{ticker}.{ext}")
                if os.path.exists(p): return p, True
        return (FB.stand_in(ticker, (prof.get(ticker) or {}).get("country_code")) if ticker else None), False

    rendered = {}
    def render_once(path, fn):
        if path not in rendered: fn(); rendered[path] = True
        return path

    def fighter_extra_facts(t):
        p = prof.get(t) or {}; out = []
        fair, price = p.get("fair_price"), p.get("price")
        if fair and price:
            fair, price = float(fair), float(price); gap = (price - fair) / fair * 100
            out.append(f"{t} fair price (model value) {R.money(fair)}, traded price {R.money(price)}, gap {gap:+.1f}%"
                       + (" (significant: worth a mention)" if abs(gap) >= FAIR_GAP else " (not significant: do not mention)"))
        fl = p.get("flow_7d") or {}
        if fl.get("buys") or fl.get("sells"):
            out.append(f"{t} trading in the last 7 days: {fl.get('buys', 0)} buys ({fl.get('shares_bought', 0)} shares), "
                       f"{fl.get('sells', 0)} sells ({fl.get('shares_sold', 0)} shares)"
                       + (" (more selling than buying)" if (fl.get("shares_sold") or 0) > (fl.get("shares_bought") or 0) else ""))
        return out

    def t7_file(t, folder):
        ph, real = photo(t)
        f = os.path.join(a.out, folder, f"T7_{t}.png")
        q = dict(prof[t]); q["price"] = float(q["price"]); q["prev_price"] = float(q["prev_price"] or q["price"])
        render_once(f, lambda: F.card(q, ph, f))
        return f, real

    def add(key, template, platform, fmt, title, event, fighters, files, alt, facts, tags, ai, flags=(), group="event"):
        if (key, platform) in done_keys: notes.append(f"skipped {key} on {platform}: already posted"); return
        posts.append(dict(key=key, template=template, platform=platform, format=fmt, title=f"{title} | {platform}", event=event,
                          fighters=fighters, files=files, alt_text=alt, facts=facts, hashtags_from=tags, ai_generated=ai,
                          flags=([AI_FLAG] if ai else []) + list(flags), group=group, slot=None))

    def bout_side(f, ok_move):
        return dict(name=f["name"], ticker=f.get("ticker"), price=f.get("price"), country_code=(prof.get(f.get("ticker")) or {}).get("country_code"),
                    old=f.get("old") if ok_move and moved(f) else None, new=f.get("new") if ok_move and moved(f) else None)

    # ---------------------------------------------------------------- leaderboard (event weeks, Half 1) and filler pool
    week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    lb = [r for r in (d.get("leaderboard") or [])][:10]
    def leaderboard_post(platform, group):
        if not lb: return
        rows = [dict(username=mask(r["username"], bl), net_worth=float(r["net_worth"]), change_pct=float(r["pct_change"]) if r.get("pct_change") is not None else None) for r in lb]
        f12 = os.path.join(a.out, "leaderboard", f"T12_{today.isoformat()}.png")
        render_once(f12, lambda: X.leaderboard(dict(title="Overall leaderboard", subtitle="Top 10 by account value, as on cagecoins.com",
                                                    period_label=dmy(today), rows=rows), f12))
        add(f"T12|overall|{week}", "T12", platform, "Single image", f"Overall leaderboard | {dmy(today)}", "", "", [f12],
            "Cage Coins overall leaderboard, top 10 players by account value: " + "; ".join(f"{i+1} {r['username']} {R.money(r['net_worth'])}" for i, r in enumerate(rows)) + ".",
            [f"Leaderboard position {i+1}: {r['username']}, account value {R.money(r['net_worth'])}, this month {r['change_pct']:+.2f}%" for i, r in enumerate(rows) if r["change_pct"] is not None]
            + ["Source: get_leaderboard('overall'), admin accounts left out, blocked usernames shown as ***."], ["#UFC", "#MMA", "#FantasyMMA"], False, group=group)
    # ---------------------------------------------------------------- HALF 1: last event review
    ig1, x1 = [], []
    if half1:
        results = [(b, *((b["red"], b["blue"]) if b["winner"] == "red" else (b["blue"], b["red"]))) for b in last["bouts"] if b.get("winner") in ("red", "blue")]
        repriced = any(moved(f) for _, w, l in results for f in (w, l))
        folder = last["id"]; es = short(last); etag = event_tag(last)
        if not repriced: notes.append(f"Half 1: {last['name']} has not been repriced, so no posts about price moves. Results card only.")
        # T11 results
        f11 = os.path.join(a.out, folder, "T11_results.png")
        render_once(f11, lambda: X.event_card(dict(name=last["name"], date=last["date"], venue=last.get("venue"), location=last.get("location"), status="completed",
                         bouts=[dict(b, red=bout_side(b["red"], repriced), blue=bout_side(b["blue"], repriced)) for b in last["bouts"]]), f11, seed=3))
        res_facts = [f"Event: {last['name']}, {dmy(last['date'])}, {last.get('venue')}, {last.get('location')}"] + [
            f"Bout {b['bout_order']} ({b['weight_class']}): {w['name']} beat {l['name']} by {method_h(b['method'])}"
            + (f", round {b['end_round']}" if b.get("end_round") else "") + ". "
            + (" | ".join(mv(f) if moved(f) and f.get("ticker") else f"{f['name']}: no price move recorded" for f in (w, l)) if repriced else "")
            for b, w, l in results]
        alt11 = f"Cage Coins results card for {last['name']} on {dmy(last['date'])}: " + "; ".join(f"{w['name']} beat {l['name']} by {method_h(b['method'])}" for b, w, l in results) + "."
        tags1 = [etag] + [name_tag(f["name"]) for b, w, l in results[:2] for f in (w, l)]
        # T10 head to head results, every main-card bout with both fighters listed
        h2h = []
        if repriced:
            for b, w, l in results:
                if not (w.get("ticker") and l.get("ticker")): continue
                (pr, rr), (pb, rb) = photo(b["red"]["ticker"]), photo(b["blue"]["ticker"])
                f10 = os.path.join(a.out, folder, f"T10_bout{b['bout_order']}.png")
                render_once(f10, lambda b=b, pr=pr, pb=pb, f10=f10: HH.card_after(dict(event=last["name"], event_date=last["date"], weight_class=b["weight_class"], is_title=b.get("is_title"),
                    winner=b["winner"], method=b["method"], round=b.get("end_round"), time=b.get("end_time"),
                    red=bout_side(b["red"], True), blue=bout_side(b["blue"], True)), pr, pb, f10))
                h2h.append((b, w, l, f10, rr or rb))
        # T7 subjects: main + co-main fighters, then big movers
        # order: main and co-main winners, then big movers (biggest first), then main and co-main losers
        subj = []
        def push(f, b):
            if f.get("ticker") in prof and f["ticker"] not in [s[0] for s in subj]: subj.append((f["ticker"], f, b))
        for b, w, l in results:
            if b["bout_order"] in (1, 2): push(w, b)
        if repriced:
            for f, b in sorted([(f, b) for b, w, l in results for f in (w, l) if f.get("ticker") in prof and moved(f) and abs(pc(f)) >= BIG_MOVE], key=lambda x: -abs(pc(x[0]))):
                push(f, b)
        for b, w, l in results:
            if b["bout_order"] in (1, 2): push(l, b)
        def t7_event_facts(t, f, b):
            w = b["red"] if b["winner"] == "red" else b["blue"]; l = b["blue"] if w is b["red"] else b["red"]
            won = f is w; opp = l if won else w
            fx = t7_facts(prof[t]) + [f"Result at {last['name']}: {f['name']} {'beat' if won else 'lost to'} {opp['name']} by {method_h(b['method'])}"
                                      + (f", round {b['end_round']}" if b.get("end_round") else "")
                                      + (" (a finish: worth naming in the caption)" if FIN.finish_kind(b.get("method")) else "")]
            if repriced and moved(f): fx.append(f"Event price move: {mv(f)}" + (" (big mover)" if abs(pc(f)) >= BIG_MOVE else ""))
            return fx + fighter_extra_facts(t)
        # Instagram: 1) results card + head to head carousel  2) fighter cards carousel  3) leaderboard
        if h2h:
            files = [f11] + [x[3] for x in h2h][:9]
            add(f"H1-IG-H2H|{last['id']}", "T11+T10", "Instagram", "Carousel", f"Results and head to heads | {es}", last["name"],
                ", ".join(f"{w['name']} ({w['ticker']}), {l['name']} ({l['ticker']})" for b, w, l, *_ in h2h), files,
                alt11 + " Then one head to head result slide per fight.", res_facts, tags1, any(x[4] for x in h2h))
        else:
            add(f"H1-IG-T11|{last['id']}", "T11", "Instagram", "Single image", f"Results card | {es}", last["name"], "", [f11], alt11, res_facts, tags1, False)
        if repriced and subj:
            cf, facts, real_any = [], [], False
            for t, f, b in subj[:10]:
                fp, real = t7_file(t, folder); cf.append(fp); real_any |= real; facts += t7_event_facts(t, f, b)
            add(f"H1-IG-T7|{last['id']}", "T7", "Instagram", "Carousel", f"Fighter cards | {es}", last["name"], ", ".join(f"{f['name']} ({t})" for t, f, b in subj[:10]), cf,
                "Carousel of Cage Coins fighter cards after " + last["name"] + ": " + "; ".join(f"{f['name']} ({t}) {R.money(float(prof[t]['price']))}" for t, f, b in subj[:10]) + ".",
                facts, [etag] + [name_tag(f["name"]) for t, f, b in subj[:3]], real_any)
        leaderboard_post("Instagram", "event")
        # X: results card, main event result, top mover, leaderboard, co-main result, other fighter cards
        add(f"H1-X-T11|{last['id']}", "T11", "X", "Single image", f"Results card | {es}", last["name"], "", [f11], alt11, res_facts, [etag], False)
        for b, w, l, f10, real in h2h[:2]:
            add(f"T10|{last['id']}|{b['bout_order']}", "T10", "X", "Single image", f"Head to head result {w['ticker']} beat {l['ticker']} | {es}", last["name"],
                f"{w['name']} ({w['ticker']}), {l['name']} ({l['ticker']})", [f10],
                f"Cage Coins head to head result: {w['name']} beat {l['name']} by {method_h(b['method'])} at {last['name'].split(':')[0]}.",
                [f"Result: {w['name']} beat {l['name']} by {method_h(b['method'])}" + (f", round {b['end_round']}" if b.get("end_round") else "") + f", {last['name']}, {dmy(last['date'])}"]
                + [mv(f) if moved(f) else f"{f['name']}: no price move recorded" for f in (w, l)] + fighter_extra_facts(w["ticker"]) + fighter_extra_facts(l["ticker"]),
                [etag, name_tag(w["name"])], real)
        leaderboard_post("X", "event")
        if repriced:
            for t, f, b in subj:
                fp, real = t7_file(t, folder)
                add(f"T7|{last['id']}|{t}", "T7", "X", "Single image", f"Fighter card {t} | {es}", last["name"], f"{f['name']} ({t})", [fp],
                    f"Cage Coins fighter card: {f['name']} ({t}), share price {R.money(float(prof[t]['price']))}.", t7_event_facts(t, f, b), [etag, name_tag(f["name"])], real)

    # ---------------------------------------------------------------- HALF 2: next event preview
    if half2:
        folder = nxt["id"]; ns = short(nxt); etag = event_tag(nxt)
        f11 = os.path.join(a.out, folder, "T11_card.png")
        render_once(f11, lambda: X.event_card(dict(name=nxt["name"], date=nxt["date"], venue=nxt.get("venue"), location=nxt.get("location"), status="upcoming",
                         bouts=[dict(b, red=bout_side(b["red"], False), blue=bout_side(b["blue"], False)) for b in nxt["bouts"]]), f11, seed=9))
        card_facts = [f"Event: {nxt['name']}, {dmy(nxt['date'])}, {nxt.get('venue')}, {nxt.get('location')}"] + [
            f"Bout {b['bout_order']} ({b['weight_class']}{' title' if b.get('is_title') else ''}): {b['red']['name']} "
            + (f"{b['red']['ticker']} {R.money(b['red']['price'])}" if b['red'].get('ticker') else "(not listed)") + f" vs {b['blue']['name']} "
            + (f"{b['blue']['ticker']} {R.money(b['blue']['price'])}" if b['blue'].get('ticker') else "(not listed)") for b in nxt["bouts"]]
        alt11 = f"Cage Coins card for {nxt['name']} on {dmy(nxt['date'])}: " + "; ".join(f"{b['red']['name']} vs {b['blue']['name']}" for b in nxt["bouts"]) + "."
        add(f"T11|{nxt['id']}", "T11", "Instagram", "Single image", f"Event card | {ns}", nxt["name"], "", [f11], alt11, card_facts, [etag], False)
        add(f"T11|{nxt['id']}", "T11", "X", "Single image", f"Event card | {ns}", nxt["name"], "", [f11], alt11, card_facts, [etag], False)
        # T9 for every bout with both fighters listed
        h2h = []
        for b in nxt["bouts"]:
            r, bb = b["red"], b["blue"]
            if not (r.get("ticker") in prof and bb.get("ticker") in prof): notes.append(f"Half 2: bout {b['bout_order']} has a fighter not in the table, no head to head."); continue
            def hside(bf):
                p = dict(prof[bf["ticker"]]); p.update(price=float(p["price"]), prev_price=float(p["prev_price"] or p["price"]),
                    rank=bf.get("rank"), champ=bf.get("champ"), ufc_w=bf.get("w"), ufc_l=bf.get("l"), streak=bf.get("streak"),
                    form=[x.get("result", "") for x in (p.get("last_fights") or [])][:5])
                return p
            hr, hb = hside(r), hside(bb); (pr, rr), (pb, rb) = photo(r["ticker"]), photo(bb["ticker"])
            f9 = os.path.join(a.out, folder, f"T9_bout{b['bout_order']}.png")
            render_once(f9, lambda b=b, hr=hr, hb=hb, pr=pr, pb=pb, f9=f9: HH.card(dict(event=nxt["name"], event_date=nxt["date"], weight_class=b["weight_class"],
                        is_title=b.get("is_title"), rounds=b["rounds"], red=hr, blue=hb), pr, pb, f9))
            def tape(p): return (f"{p['name']} {p['ticker']} {R.money(p['price'])}, rank {R.rank_txt(p.get('rank'), p.get('champ'))}, pro {p['wins']}-{p['losses']}, UFC {p['ufc_w']}-{p['ufc_l']}, "
                                 f"{t7_rec(p)[1] or 'method split not recorded'}, win streak {p.get('streak') or 0}, last results {' '.join(p['form'])}")
            facts = [f"Bout {b['bout_order']}: {b['weight_class']}{' title fight' if b.get('is_title') else ''}, {b['rounds']} rounds, {nxt['name']} {dmy(nxt['date'])}",
                     "Red: " + tape(hr), "Blue: " + tape(hb)] + fighter_extra_facts(r["ticker"]) + fighter_extra_facts(bb["ticker"])
            h2h.append((b, hr, hb, f9, rr or rb, facts))
        if h2h:
            add(f"H2-IG-T9|{nxt['id']}", "T9", "Instagram", "Carousel", f"Head to heads | {ns}", nxt["name"],
                ", ".join(f"{hr['name']} ({hr['ticker']}) v {hb['name']} ({hb['ticker']})" for b, hr, hb, *_ in h2h), [x[3] for x in h2h][:10],
                f"Carousel of Cage Coins head to head cards for {nxt['name']}, one per fight, with both fighters' current share prices.",
                [f for x in h2h for f in x[5]] + ["Prices are as of the query time and can change before the fight."],
                [etag] + [name_tag(x[1]["name"]) for x in h2h[:2]], any(x[4] for x in h2h))
        # T7: main and co-main fighters, then prospects
        main4 = [f["ticker"] for b in nxt["bouts"] if b["bout_order"] in (1, 2) for f in (b["red"], b["blue"]) if f.get("ticker") in prof]
        pros = [f for b in nxt["bouts"] if b["bout_order"] > 2 for f in (b["red"], b["blue"])
                if f.get("ticker") in prof and not f.get("champ") and f.get("rank") in (None, 99) and ((f.get("streak") or 0) >= 2 or (f.get("l") == 0 and (f.get("w") or 0) >= 1))]
        pros = [f["ticker"] for f in sorted(pros, key=lambda f: (-(f.get("streak") or 0), -(f.get("w") or 0)))][:3]
        def t7_pre_facts(t): return t7_facts(prof[t]) + fighter_extra_facts(t) + [f"Fights at {nxt['name']} on {dmy(nxt['date'])}"]
        for group, ticks, label in (("main", main4, "Main and co-main"), ("prospects", pros, "Prospects")):
            if not ticks: continue
            files, facts, real_any = [], [], False
            for t in ticks:
                fp, real = t7_file(t, folder); files.append(fp); facts += t7_pre_facts(t); real_any |= real
            if group == "prospects": facts.append("Prospect rule: unranked, not a champion, on the main card outside the top two fights, win streak of 2+ or unbeaten in the UFC.")
            add(f"H2-IG-T7-{group}|{nxt['id']}", "T7", "Instagram", "Carousel", f"{label} fighter cards | {ns}", nxt["name"], ", ".join(f"{prof[t]['name']} ({t})" for t in ticks), files,
                f"Carousel of Cage Coins fighter cards ({label.lower()}) for {nxt['name']}: " + "; ".join(f"{prof[t]['name']} ({t}) {R.money(float(prof[t]['price']))}" for t in ticks) + ".",
                facts, [etag] + [name_tag(prof[t]["name"]) for t in ticks[:2]], real_any)
        # X: head to heads for the top two fights, the four main fighters, then prospects, then other head to heads
        for b, hr, hb, f9, real, facts in h2h[:2]:
            add(f"T9|{nxt['id']}|{b['bout_order']}", "T9", "X", "Single image", f"Head to head {hr['ticker']} v {hb['ticker']} | {ns}", nxt["name"], f"{hr['name']} ({hr['ticker']}), {hb['name']} ({hb['ticker']})", [f9],
                f"Cage Coins head to head for {nxt['name']}: {hr['name']} ({hr['ticker']}) at {R.money(hr['price'])} against {hb['name']} ({hb['ticker']}) at {R.money(hb['price'])}.",
                facts + ["Prices are as of the query time and can change before the fight."], [etag, name_tag(hr["name"])], real)
        for t in main4 + pros:
            fp, real = t7_file(t, folder)
            add(f"T7|{nxt['id']}|{t}", "T7", "X", "Single image", f"Fighter card {t} | {ns}", nxt["name"], f"{prof[t]['name']} ({t})", [fp],
                f"Cage Coins fighter card: {prof[t]['name']} ({t}), share price {R.money(float(prof[t]['price']))}.", t7_pre_facts(t), [etag, name_tag(prof[t]["name"])], real)
        for b, hr, hb, f9, real, facts in h2h[2:]:
            add(f"T9|{nxt['id']}|{b['bout_order']}", "T9", "X", "Single image", f"Head to head {hr['ticker']} v {hb['ticker']} | {ns}", nxt["name"], f"{hr['name']} ({hr['ticker']}), {hb['name']} ({hb['ticker']})", [f9],
                f"Cage Coins head to head for {nxt['name']}: {hr['name']} ({hr['ticker']}) at {R.money(hr['price'])} against {hb['name']} ({hb['ticker']}) at {R.money(hb['price'])}.",
                facts + ["Prices are as of the query time and can change before the fight."], [etag, name_tag(hr["name"])], real)


    risers = [r for r in (d.get("risers_7d") or []) if r.get("old") and r.get("new")]
    for r in risers: r["pct"] = (float(r["new"]) - float(r["old"])) / float(r["old"]) * 100
    def filler(platform):
        """Filler candidates in order: leaderboard (once a week), big growers (once a week), T7 of a fighter doing well (14-day cooldown)."""
        out = []
        if lb: out.append(("lb", None))
        if risers: out.append(("growers", None))
        recent = {e.get("ticker") for e in log if e.get("template") == "T7" and e["platform"] == platform
                  and (today - ddate(e["date"])).days < COOLDOWN_DAYS}
        for r in risers:
            if r["ticker"] in prof and r["ticker"] not in recent and r["pct"] > 0: out.append(("t7", r))
        return out
    def make_filler(kind, r, platform):
        before = len(posts)
        if kind == "lb": leaderboard_post(platform, "filler")
        elif kind == "growers":
            f13 = os.path.join(a.out, "growers", f"T13_{today.isoformat()}.png")
            rows = [dict(ticker=x["ticker"], name=x["name"], old=float(x["old"]), new=float(x["new"]), pct=x["pct"]) for x in risers[:10]]
            render_once(f13, lambda: X.growers(dict(title="Big growers", subtitle="Biggest price rises in the last 7 days", period_label=dmy(today), rows=rows), f13))
            add(f"T13|{week}", "T13", platform, "Single image", f"Big growers | {dmy(today)}", "", ", ".join(x["ticker"] for x in rows), [f13],
                "Cage Coins big growers, biggest price rises in the last 7 days: " + "; ".join(f"{x['ticker']} {x['pct']:+.1f} percent" for x in rows) + ".",
                [f"{x['ticker']} {x['name']}: {R.money(float(x['old']))} seven days ago, {R.money(x['new'])} now ({x['pct']:+.1f}%)" for x in rows],
                ["#UFC", "#MMA"], False, group="filler")
        elif kind == "t7":
            t = r["ticker"]; fp, real = t7_file(t, "filler")
            add(f"T7|filler|{t}|{today.isoformat()}", "T7", platform, "Single image", f"Fighter card {t} (doing well) | {dmy(today)}", "", f"{prof[t]['name']} ({t})", [fp],
                f"Cage Coins fighter card: {prof[t]['name']} ({t}), share price {R.money(float(prof[t]['price']))}.",
                t7_facts(prof[t]) + [f"7-day move: {t} {R.money(float(r['old']))} to {R.money(float(r['new']))} ({r['pct']:+.1f}%)"] + fighter_extra_facts(t),
                ["#UFC", name_tag(prof[t]["name"])], real, group="filler")
        return len(posts) > before

    # ---------------------------------------------------------------- monthly posts on the 1st
    if monthly:
        prev = (today.replace(day=1) - dt.timedelta(days=1))
        snaps = sorted(f for f in os.listdir(a.snapshots) if f.startswith(prev.strftime("%Y-%m")) and f.endswith(".json"))
        mon = prev.strftime("%B %Y")
        if not snaps: notes.append(f"Monthly: no snapshot saved during {mon}, so no monthly posts.")
        else:
            snap = json.load(open(os.path.join(a.snapshots, snaps[-1]))); asof = dmy(snaps[-1][:10])
            m = [r for r in (snap.get("leaderboard_monthly") or []) if r.get("pct_change") is not None]
            if m:
                top = m[0]; u = mask(top["username"], bl)
                f6 = os.path.join(a.out, "monthly", f"T6_{prev.strftime('%Y-%m')}.png")
                render_once(f6, lambda: X.monthly_winner(dict(period_label=f"{mon} · as of {asof}", username=u, return_pct=float(top["pct_change"]), net_worth=float(top["net_worth"])), f6))
                rows = [dict(username=mask(r["username"], bl), net_worth=float(r["net_worth"]), change_pct=float(r["pct_change"])) for r in m[:10]]
                f12m = os.path.join(a.out, "monthly", f"T12_{prev.strftime('%Y-%m')}.png")
                render_once(f12m, lambda: X.leaderboard(dict(title=f"{prev.strftime('%B')} leaderboard", subtitle="Best return this month, as on cagecoins.com",
                                                             period_label=f"as of {asof}", change_label="MONTH", rows=rows), f12m))
                mf = [f"Monthly standings for {mon} from the last snapshot, {asof} (the site resets monthly figures at midnight on the 1st)",
                      f"Trader of the month: {u}, return {float(top['pct_change']):+.2f}%, account value {R.money(float(top['net_worth']))}"] + \
                     [f"Monthly position {i+1}: {r['username']}, {r['change_pct']:+.2f}%" for i, r in enumerate(rows)]
                for plat in ("Instagram", "X"):
                    files = [f6, f12m] if plat == "Instagram" else [f6]
                    add(f"T6|{prev.strftime('%Y-%m')}", "T6", plat, "Carousel" if plat == "Instagram" else "Single image", f"Trader of the month | {mon}", "", "", files,
                        f"Cage Coins trader of the month for {mon}: {u}, return {float(top['pct_change']):+.2f} percent." + (" Then the monthly top 10." if plat == "Instagram" else ""),
                        mf, ["#UFC", "#MMA", "#FantasyMMA"], False, group="monthly")

    # ---------------------------------------------------------------- slots
    def at(day, hhmm): return f"{day.isoformat()}T{hhmm}"
    for p in posts:
        if p["group"] == "monthly": p["slot"] = at(today, MONTHLY_SLOT)
    for plat in ("Instagram", "X"):
        free = [at(day, s) for day in days for s in slots_by_day[plat]]
        if half2: free = [s for s in free if s[:10] <= nxt["date"][:10]]
        queue = [p for p in posts if p["platform"] == plat and p["group"] in ("event",)]
        for p in queue:
            if free: p["slot"] = free.pop(0)
        dropped = [p for p in queue if p["slot"] is None]
        for p in dropped: notes.append(f"not enough slots: {p['key']} on {plat} left for a later run"); posts.remove(p)
        for kind, r in filler(plat):
            if not free: break
            if make_filler(kind, r, plat): posts[-1]["slot"] = free.pop(0)
        if free: notes.append(f"{plat}: {len(free)} slot(s) left empty, nothing new to post: " + ", ".join(free))
    posts = [p for p in posts if p["slot"]]
    posts.sort(key=lambda p: (p["slot"], p["platform"]))
    os.makedirs(a.out, exist_ok=True)
    json.dump(dict(generated_at=d.get("generated_at"), today=today.isoformat(), half1=bool(half1), half2=bool(half2), monthly=monthly,
                   posts=posts, notes=notes), open(os.path.join(a.out, "manifest.json"), "w"), indent=1, ensure_ascii=False)
    print(f"{len(posts)} posts, {sum(len(p['files']) for p in posts)} images. Half 1: {bool(half1)}. Half 2: {bool(half2)}. Monthly: {monthly}.")
    for p in posts: print(f"  {p['slot']}  {p['platform']:<9} {p['template']:<8} {p['title']}")
    for n in notes: print(" -", n)

if __name__ == "__main__": main()
