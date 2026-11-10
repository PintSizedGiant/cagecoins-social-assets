#!/usr/bin/env python3
"""Turn raw.json (result of tools/query.sql) into rendered cards plus manifest.json.

  python3 tools/build.py raw.json --set recap preview midweek trader --out build [--photos-ok WLKR,GANE]

Sets:  recap   = T3 carousel + T4 movers + T1 top riser     (needs the last event to be repriced)
       preview = T2 matchup for the next event's main event (and co-main when it is a title fight)
       midweek = T5 prospect watch
       trader  = T6 top trader of the month
The manifest lists every post with its files, the exact numbers used, alt text, and any flags.
Nothing here writes captions: the facts in the manifest are the only numbers a caption may use."""
import argparse, json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_render as R

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START_CASH = "$2,000"

def load(path):
    d = json.load(open(path))
    while isinstance(d, (dict, list)):
        if isinstance(d, dict) and "last" in d and "next" in d: return d
        if isinstance(d, dict) and "rows" in d: d = d["rows"]
        elif isinstance(d, list) and d: d = d[0]
        elif isinstance(d, dict) and "d" in d: d = d["d"]
        else: break
    sys.exit("raw.json does not look like the result of tools/query.sql")

def dmy(iso): y, m, d = str(iso)[:10].split("-"); return f"{d}/{m}/{y}"
def short(ev): return ("FIGHT NIGHT" if ev["name"].upper().startswith("UFC FIGHT NIGHT") else ev["name"].split(":")[0].upper()) + " · " + dmy(ev["date"])
def method_h(m):
    if not m: return "unknown method"
    if m.lower().startswith("decision"):
        kind = m.split("-")[-1].strip().lower() if "-" in m else ""
        return (kind + " decision").strip()
    return m
def moved(f): return f.get("old") is not None and f.get("new") is not None and float(f["old"]) > 0
def num(f, *keys):
    for k in keys:
        if f.get(k) is not None: f[k] = float(f[k])
    return f
def photo_for(ticker, ok):
    if not ticker or ticker not in ok: return None
    for ext in ("png", "webp", "avif"):
        p = os.path.join(REPO, "photos", f"{ticker}.{ext}")
        if os.path.exists(p): return p
    return None
def pc(f): return R.pct(f["old"], f["new"])
def mv(f): return f"{f['ticker']} {f['name']}: {R.money(f['old'])} to {R.money(f['new'])} ({pc(f):+.1f}%)"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw"); ap.add_argument("--set", nargs="+", required=True, choices=["recap", "preview", "midweek", "trader"])
    ap.add_argument("--out", default="build"); ap.add_argument("--photos-ok", default="")
    a = ap.parse_args()
    d = load(a.raw); ok = {t.strip().upper() for t in a.photos_ok.split(",") if t.strip()}
    posts, notes = [], []
    last, nxt = d.get("last"), d.get("next")
    for ev in (last, nxt):
        for b in (ev or {}).get("bouts") or []:
            num(b["red"], "price", "old", "new"); num(b["blue"], "price", "old", "new")
    def add(key, template, platforms, fmt, title, event, fighters, files, alt, facts, flags=()):
        posts.append(dict(key=key, template=template, platforms=platforms, format=fmt, title=title, event=event,
                          fighters=fighters, files=files, alt_text=alt, facts=facts, flags=list(flags)))

    # ------------------------------------------------------------------ recap + midweek need the last event
    results = []   # (bout, winner, loser)
    if last and last.get("bouts"):
        for b in last["bouts"]:
            if b["winner"] in ("red", "blue"):
                w, l = (b["red"], b["blue"]) if b["winner"] == "red" else (b["blue"], b["red"])
                results.append((b, w, l))
            else: notes.append(f"{last['name']}: bout {b['bout_order']} ({b['red']['name']} vs {b['blue']['name']}) has no winner recorded, left out.")
    movers = [f for _, w, l in results for f in (w, l) if moved(f) and f.get("ticker")]
    repriced = len(movers) > 0
    if last: odir = os.path.join(a.out, last["id"]); es = short(last)

    if "recap" in a.set:
        if not last or not results: notes.append("recap: no completed event with results found.")
        elif not repriced: notes.append(f"recap: {last['name']} has no event-linked price moves yet. Run the pricing skill first, then rerun.")
        else:
            # T3 carousel
            files, flags = [], []
            best = max(movers, key=pc)
            name_lines = [s.strip() for s in last["name"].split(":", 1)]
            f0 = os.path.join(odir, "T3_01_cover.png")
            R.t3a(dict(date=dmy(last["date"]), event_lines=name_lines, venue=" · ".join(x for x in [last.get("venue"), (last.get("location") or "").split(",")[0]] if x),
                       stats=[("FIGHTS", str(len(results))), ("PRICE MOVES", str(len(movers))), ("TOP RISER", best["ticker"])]), f0); files.append(f0)
            facts = [f"Event: {last['name']}, {dmy(last['date'])}, {last.get('venue')}, {last.get('location')}", f"Fights on main card with a result: {len(results)}", f"Price moves: {len(movers)}", f"Top riser: {mv(best)}"]
            for i, (b, w, l) in enumerate(results[:8], start=2):
                tag = "Main event" if b["bout_order"] == 1 else ("Co-main" if b["bout_order"] == 2 else "Main card")
                def side(f):
                    if moved(f): return dict(name=f["name"], ticker=f.get("ticker"), old=f["old"], new=f["new"])
                    return dict(name=f["name"], ticker=f.get("ticker"), price=f.get("price"))
                fp = os.path.join(odir, f"T3_{i:02d}_bout{b['bout_order']}.png")
                R.t3b(dict(event_short=es, tag=tag, weight_class=b["weight_class"] + (" title fight" if b.get("is_title") else ""), winner=side(w), loser=side(l),
                           method_line=f"{w['name']} won by {method_h(b['method'])}", time_line=f"Round {b['end_round']} · {b['end_time']}"), fp); files.append(fp)
                facts.append(f"Bout {b['bout_order']} ({b['weight_class']}): {w['name']} beat {l['name']} by {method_h(b['method'])}, round {b['end_round']}, {b['end_time']}. " +
                             " | ".join(mv(f) if moved(f) and f.get("ticker") else f"{f['name']}: no price move recorded" for f in (w, l)))
                for f in (w, l):
                    if not f.get("ticker"): flags.append(f"{f['name']} is not in the fighters table, so the slide shows 'not listed'.")
                    elif not moved(f): flags.append(f"{f['name']} ({f['ticker']}) fought at this event but has no event-linked price move. Check the pricing run.")
            fl = os.path.join(odir, f"T3_{len(files)+1:02d}_close.png")
            R.t3c(dict(start_cash=START_CASH, next_line=(f"NEXT: {nxt['name'].upper().replace(':', ' ·')} · {dmy(nxt['date'])}" if nxt else "")), fl); files.append(fl)
            add(f"T3|{last['id']}", "T3", ["Instagram"], "Carousel", f"T3 recap carousel | {es}", last["name"], ", ".join(f"{f['name']} ({f['ticker']})" for f in movers),
                files, f"Carousel of {len(files)} slides showing how Cage Coins fighter prices moved after {last['name']} on {dmy(last['date'])}. Top riser {best['ticker']} {best['name']}, {pc(best):+.1f} percent.", facts, flags)
            # T4 movers
            srt = sorted(movers, key=pc, reverse=True)
            risers = [f for f in srt if f["new"] > f["old"]][:5]; fallers = [f for f in srt[::-1] if f["new"] < f["old"]][:5]
            f4 = os.path.join(odir, "T4_movers.png")
            R.t4(dict(label=es, title="Biggest movers", risers=risers, fallers=fallers), f4)
            add(f"T4|{last['id']}", "T4", ["Instagram", "X"], "Single image", f"T4 biggest movers | {es}", last["name"], ", ".join(f["ticker"] for f in risers + fallers), [f4],
                f"Table of the biggest Cage Coins price movers after {last['name']}. Risers: " + "; ".join(f"{f['ticker']} {pc(f):+.1f} percent" for f in risers) + ". Fallers: " + "; ".join(f"{f['ticker']} {pc(f):+.1f} percent" for f in fallers) + ".",
                ["Risers: " + "; ".join(mv(f) for f in risers), "Fallers: " + "; ".join(mv(f) for f in fallers)])
            # T1 top riser
            b, w, l = next(r for r in results if r[1] is best or r[2] is best)
            opp = l if w is best else w; won = w is best
            card = dict(label=es, ticker=best["ticker"], division=best.get("division") or b["weight_class"], name=best["name"], old=best["old"], new=best["new"],
                        result_head=f"{'Beat' if won else 'Lost to'} {opp['name']}", result_sub=f"{method_h(b['method']).capitalize() if method_h(b['method']).islower() else method_h(b['method'])} · Round {b['end_round']} · {b['end_time']}",
                        rank=R.rank_txt(best.get("rank"), best.get("champ")), country=best.get("country") or "")
            f1 = os.path.join(odir, f"T1_{best['ticker']}.png"); ph = photo_for(best["ticker"], ok)
            if ph: R.t1p(card, ph, f1)
            else: R.t1(card, f1)
            add(f"T1|{last['id']}|{best['ticker']}", "T1p" if ph else "T1", ["Instagram", "X"], "Single image", f"T1 mover {best['ticker']} | {es}", last["name"], f"{best['name']} ({best['ticker']})", [f1],
                f"Cage Coins price card: {best['ticker']}, {best['name']}, {pc(best):+.1f} percent, from {R.money(best['old'])} to {R.money(best['new'])} after {'beating' if won else 'losing to'} {opp['name']}.",
                [mv(best), f"Result: {best['name']} {'beat' if won else 'lost to'} {opp['name']} by {method_h(b['method'])}, round {b['end_round']}, {b['end_time']}, {last['name']} {dmy(last['date'])}", f"Photo used: {'yes, photos/' + os.path.basename(ph) if ph else 'no'}"])

    if "midweek" in a.set:
        cands = [(b, w, l) for b, w, l in results if moved(w) and w.get("ticker") and w["new"] > w["old"] and not w.get("champ") and w.get("rank") in (None, 99)]
        if not cands: notes.append("midweek: no unranked winner with a price rise at the last event, so no T5 prospect card.")
        else:
            b, w, l = max(cands, key=lambda r: ((r[1].get("streak") or 0), pc(r[1])))
            f5 = os.path.join(odir, f"T5_{w['ticker']}.png"); mh = method_h(b["method"])
            R.t5(dict(ticker=w["ticker"], name=w["name"], division=w.get("division") or b["weight_class"], country=w.get("country") or "", price=w["new"], old=w["old"],
                      stats=[("UFC RECORD", f"{w['w']}-{w['l']}"), ("WIN STREAK", f"W{w.get('streak') or 0}"), ("LAST WIN", f"{'DEC' if 'decision' in mh else mh} R{b['end_round']}")],
                      last_head=f"Beat {l['name']}", last_sub=f"{mh} · Round {b['end_round']} · {b['end_time']} · {dmy(last['date'])}"), f5)
            add(f"T5|{last['id']}|{w['ticker']}", "T5", ["Instagram", "X"], "Single image", f"T5 prospect {w['ticker']} | {es}", last["name"], f"{w['name']} ({w['ticker']})", [f5],
                f"Cage Coins prospect card: {w['ticker']}, {w['name']}, {w.get('division')}, price {R.money(w['new'])}, UFC record {w['w']}-{w['l']}, win streak {w.get('streak')}.",
                [mv(w), f"UFC record {w['w']}-{w['l']}, win streak {w.get('streak')}, unranked", f"Last result: beat {l['name']} by {mh}, round {b['end_round']}, {b['end_time']}, {dmy(last['date'])}",
                 "Chosen by rule: unranked winner at the last event with a price rise, longest win streak first, then biggest rise."])

    if "preview" in a.set:
        if not nxt or not nxt.get("bouts"): notes.append("preview: no upcoming event with bouts found.")
        else:
            ndir = os.path.join(a.out, nxt["id"]); ns = short(nxt)
            for b in nxt["bouts"]:
                if not (b["bout_order"] == 1 or (b["bout_order"] == 2 and b.get("is_title"))): continue
                missing = [f["name"] for f in (b["red"], b["blue"]) if not f.get("ticker") or f.get("price") is None]
                if missing:
                    notes.append(f"preview: bout {b['bout_order']} of {nxt['name']} skipped because {', '.join(missing)} is not in the fighters table."); continue
                kick = "Main event" if b["bout_order"] == 1 else "Co-main event"
                line = f"{b['weight_class']}{' title fight' if b.get('is_title') else ''} · {b['rounds']} rounds"
                fp = os.path.join(ndir, f"T2_bout{b['bout_order']}.png")
                R.t2(dict(event_label=ns, kicker=kick, bout_line=line, red=b["red"], blue=b["blue"]), fp)
                r, bl = b["red"], b["blue"]; hi, lo = sorted([r, bl], key=lambda f: -f["price"])
                add(f"T2|{nxt['id']}|{b['bout_order']}", "T2", ["Instagram", "X"], "Single image", f"T2 matchup {r['ticker']} v {bl['ticker']} | {ns}", nxt["name"], f"{r['name']} ({r['ticker']}), {bl['name']} ({bl['ticker']})", [fp],
                    f"Cage Coins matchup card for {nxt['name']}: {r['name']} ({r['ticker']}) at {R.money(r['price'])} against {bl['name']} ({bl['ticker']}) at {R.money(bl['price'])}.",
                    [f"Event: {nxt['name']}, {dmy(nxt['date'])}, {nxt.get('venue')}, {nxt.get('location')}", f"{kick}: {line}",
                     f"Red: {r['name']} {r['ticker']} {R.money(r['price'])}, rank {R.rank_txt(r.get('rank'), r.get('champ'))}, UFC {r['w']}-{r['l']}, {r.get('country')}",
                     f"Blue: {bl['name']} {bl['ticker']} {R.money(bl['price'])}, rank {R.rank_txt(bl.get('rank'), bl.get('champ'))}, UFC {bl['w']}-{bl['l']}, {bl.get('country')}",
                     f"{hi['ticker']} trades at {hi['price']/lo['price']:.1f}x the price of {lo['ticker']}", "Prices are as of the query time and can change before the fight."])

    if "trader" in a.set:
        tr = [t for t in (d.get("traders") or []) if t.get("month_start_value") and float(t["month_start_value"]) > 0]
        for t in tr: t["ret"] = (float(t["net_worth"]) - float(t["month_start_value"])) / float(t["month_start_value"]) * 100
        tr = [t for t in tr if t["ret"] > 0]
        if not tr: notes.append("trader: no non-admin player with a positive return this month, so no T6 card.")
        else:
            t = max(tr, key=lambda x: x["ret"]); y, m, _ = str(t["month_start"])[:10].split("-")
            mon = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"][int(m) - 1]
            f6 = os.path.join(a.out, "trader", f"T6_{y}-{m}.png")
            R.t6(dict(period_label=f"{mon} {y}", title="Top trader this month", username=t["username"], return_label="RETURN THIS MONTH", return_pct=t["ret"], net_worth=float(t["net_worth"]), start_cash=START_CASH), f6)
            add(f"T6|{y}-{m}", "T6", ["Instagram", "X"], "Single image", f"T6 top trader | {mon.title()} {y}", "", "", [f6],
                f"Cage Coins top trader card for {mon.title()} {y}: {t['username']}, return {t['ret']:+.2f} percent, account value {R.money(float(t['net_worth']))}.",
                [f"Username: {t['username']}", f"Return this month: {t['ret']:+.2f}% (from {R.money(float(t['month_start_value']))} to {R.money(float(t['net_worth']))})", "Admin accounts are excluded.", f"Players with a positive return this month: {len(tr)}"])

    os.makedirs(a.out, exist_ok=True)
    json.dump(dict(generated_at=d.get("generated_at"), posts=posts, notes=notes), open(os.path.join(a.out, "manifest.json"), "w"), indent=1, ensure_ascii=False)
    print(f"{len(posts)} posts, {sum(len(p['files']) for p in posts)} images. Notes: {len(notes)}")
    for n in notes: print(" -", n)

if __name__ == "__main__": main()
