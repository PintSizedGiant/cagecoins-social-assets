"""Cage Coins templates added for the daily plan (13/11/2026), in the T7 to T10 visual style.
T11 event card (before or after the event), T12 leaderboard, T6 monthly winner (restyled).
1080x1350 PNG, no metadata."""
import os
from PIL import Image, ImageDraw
import cc_fighter as F
from cc_fighter import W, H, M, WHITE, SOFT, MUTED, GREEN, RED, GREY, YELLOW, bc, fit, money, flag, DIV

GOLD = (250, 204, 21)
PANEL = (10, 24, 19)
LINE = (38, 60, 50)

def _save(im, out):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    im.convert("RGB").save(out, "PNG", optimize=True)

def _header(dr, right):
    dr.text((M, 40), "CAGECOINS", font=bc(800, 58), fill=WHITE)
    f = fit(dr, right, 600, 28, 560); dr.text((W - M - dr.textlength(right, font=f), 54), right, font=f, fill=SOFT)

def _footer(dr):
    dr.text((M, H - 74), "cagecoins.com", font=bc(700, 30), fill=GREEN)
    t = "Fantasy money only · Not affiliated with the UFC"; f = bc(600, 22)
    dr.text((W - M - dr.textlength(t, font=f), H - 66), t, font=f, fill=MUTED)

def _pct(old, new): return (new - old) / old * 100 if old else 0.0

def _side(dr, im, x, y, s, align_right, state):
    """state: None (before), 'W' or 'L' (after)."""
    name = s.get("name") or "TBC"; tick = s.get("ticker")
    col_name = WHITE if state != "L" else MUTED
    fl = flag(s.get("country_code"), 30)
    nf = fit(dr, name.upper(), 800, 40, 330)
    nw = dr.textlength(name.upper(), font=nf)
    if align_right:
        nx = x - nw
        if fl: im.paste(fl, (int(nx - fl.width - 12), y + 8), fl)
    else:
        nx = x
        if fl: im.paste(fl, (int(nx), y + 8), fl); nx += fl.width + 12
    dr.text((nx, y), name.upper(), font=nf, fill=col_name)
    if state is None:
        line = f"{tick}  {money(s['price'])}" if tick and s.get("price") is not None else "Not listed yet"
        lc = SOFT
    elif s.get("old") is not None and s.get("new") is not None:
        p = _pct(s["old"], s["new"]); lc = GREEN if p >= 0 else RED
        line = f"{tick}  {money(s['new'])}  {'+' if p >= 0 else ''}{p:.1f}%"
    else:
        line = f"{tick}  no price move recorded" if tick else "Not listed"; lc = MUTED
    lf = bc(700, 28); lw = dr.textlength(line, font=lf)
    dr.text((x - lw if align_right else x, y + 50), line, font=lf, fill=lc)

def event_card(e, out, seed=7):
    """e: name date venue location status('upcoming'|'completed') bouts[{weight_class is_title winner method end_round red{} blue{}}]
       fighter: name ticker price country_code old new"""
    after = e.get("status") == "completed"
    im = F.background(seed, line_col=(74, 222, 128))
    shade = Image.new("RGBA", (W, H), (4, 9, 8, 175)); im.paste(shade, (0, 0), shade)
    dr = ImageDraw.Draw(im)
    _header(dr, "RESULTS" if after else "THIS WEEK")
    title, _, sub = str(e["name"]).partition(":")
    dr.text((M, 130), title.strip().upper(), font=fit(dr, title.strip().upper(), 800, 104, W - 2 * M), fill=WHITE)
    if sub.strip(): dr.text((M, 244), sub.strip().upper(), font=fit(dr, sub.strip().upper(), 700, 56, W - 2 * M), fill=GREEN)
    y_, m_, d_ = str(e["date"])[:10].split("-")
    meta = f"{d_}/{m_}/{y_}  ·  {e.get('venue') or ''}  ·  {e.get('location') or ''}".strip(" ·")
    dr.text((M, 316), meta, font=fit(dr, meta, 600, 30, W - 2 * M), fill=SOFT)
    dr.text((M, 376), "MAIN CARD", font=bc(700, 26), fill=MUTED)
    bouts = e["bouts"][:6]
    top, bottom = 414, H - 110
    rh = min(140, (bottom - top) // max(1, len(bouts)))
    for i, b in enumerate(bouts):
        y = top + i * rh
        dr.rounded_rectangle([M, y, W - M, y + rh - 14], 16, fill=PANEL, outline=LINE, width=2)
        if b.get("is_title"): dr.rectangle([M + 2, y + 2, M + 8, y + rh - 16], fill=GOLD)
        rs = bs = None
        if after and b.get("winner") in ("red", "blue"):
            rs, bs = ("W", "L") if b["winner"] == "red" else ("L", "W")
        cy = y + (rh - 14) // 2 - 40
        _side(dr, im, M + 28, cy, b["red"], False, rs)
        _side(dr, im, W - M - 28, cy, b["blue"], True, bs)
        mid = DIV.get(b.get("weight_class"), (b.get("weight_class") or "").upper())
        if b.get("is_title"): mid += " TITLE"
        mf = bc(700, 22); dr.text(((W - dr.textlength(mid, font=mf)) / 2, cy + 4), mid, font=mf, fill=GOLD if b.get("is_title") else MUTED)
        if after and b.get("method"):
            m = b["method"].split(" - ")[0].upper().replace("DECISION", "DEC")
            if b.get("end_round"): m += f" R{b['end_round']}"
        else:
            m = "VS"
        cf = bc(800, 34); dr.text(((W - dr.textlength(m, font=cf)) / 2, cy + 34), m, font=cf, fill=WHITE)
    _footer(dr)
    _save(im, out)

def leaderboard(d, out, seed=11):
    """d: title period_label rows[{username net_worth change_pct (or None)}]  (top 10, already sorted)"""
    im = F.background(seed)
    shade = Image.new("RGBA", (W, H), (4, 9, 8, 170)); im.paste(shade, (0, 0), shade)
    dr = ImageDraw.Draw(im)
    _header(dr, d["period_label"].upper())
    dr.text((M, 130), d["title"].upper(), font=fit(dr, d["title"].upper(), 800, 96, W - 2 * M), fill=WHITE)
    dr.text((M, 236), d.get("subtitle", ""), font=bc(600, 30), fill=SOFT)
    rows = d["rows"][:10]
    top = 310; rh = min(92, (H - 120 - top) // max(1, len(rows)))
    dr.text((M + 120, top - 34), "PLAYER", font=bc(700, 22), fill=MUTED)
    lab = "ACCOUNT VALUE"; dr.text((W - M - 300 - dr.textlength(lab, font=bc(700, 22)), top - 34), lab, font=bc(700, 22), fill=MUTED)
    lab = d.get("change_label", "THIS MONTH"); dr.text((W - M - 24 - dr.textlength(lab, font=bc(700, 22)), top - 34), lab, font=bc(700, 22), fill=MUTED)
    for i, r in enumerate(rows):
        y = top + i * rh
        hi = i == 0
        dr.rounded_rectangle([M, y, W - M, y + rh - 10], 14, fill=(28, 26, 8) if hi else PANEL, outline=GOLD if hi else LINE, width=2)
        cy = y + (rh - 10) // 2
        n = f"{i + 1}"; nf = bc(800, 44); dr.text((M + 34, cy - 28), n, font=nf, fill=GOLD if hi else SOFT)
        uf = fit(dr, r["username"], 700, 42, 420); dr.text((M + 120, cy - 26), r["username"], font=uf, fill=WHITE)
        v = money(r["net_worth"]); vf = bc(700, 38); dr.text((W - M - 300 - dr.textlength(v, font=vf), cy - 24), v, font=vf, fill=WHITE)
        if r.get("change_pct") is not None:
            p = r["change_pct"]; c = GREEN if p > 0 else RED if p < 0 else SOFT
            t = f"{'+' if p > 0 else ''}{p:.2f}%"
        else:
            t, c = "n/a", MUTED
        tf = bc(700, 36); dr.text((W - M - 24 - dr.textlength(t, font=tf), cy - 22), t, font=tf, fill=c)
    _footer(dr)
    _save(im, out)

def monthly_winner(d, out, seed=5):
    """d: period_label username return_pct net_worth  (return_pct straight from get_leaderboard('monthly'))"""
    im = F.background(seed)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([140, 200, 940, 900], fill=GOLD + (28,))
    from PIL import ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(140)); im.paste(glow, (0, 0), glow)
    dr = ImageDraw.Draw(im)
    _header(dr, d["period_label"].upper())
    dr.text((M, 170), "TRADER OF THE MONTH", font=bc(800, 44), fill=GOLD)
    dr.text((M, 230), d["username"], font=fit(dr, d["username"], 800, 200, W - 2 * M), fill=WHITE)
    dr.rounded_rectangle([M, 560, W - M, 860], 22, fill=PANEL, outline=GOLD, width=3)
    dr.text((M + 44, 592), "RETURN THIS MONTH", font=bc(700, 30), fill=MUTED)
    p = d["return_pct"]; col = GREEN if p >= 0 else RED
    t = f"{'+' if p >= 0 else ''}{p:.2f}%"
    dr.text((M + 44, 630), t, font=fit(dr, t, 800, 190, W - 2 * M - 88), fill=col)
    dr.text((M, 910), "ACCOUNT VALUE NOW", font=bc(700, 28), fill=MUTED)
    dr.text((M, 946), money(d["net_worth"]), font=bc(800, 72), fill=WHITE)
    note = "Return as shown on the Cage Coins monthly leaderboard."
    dr.text((M, 1060), note, font=bc(600, 28), fill=SOFT)
    _footer(dr)
    _save(im, out)

def growers(d, out, seed=13):
    """T13 big growers. d: title subtitle period_label rows[{ticker name new pct}] (top 10, sorted)"""
    im = F.background(seed)
    shade = Image.new("RGBA", (W, H), (4, 9, 8, 170)); im.paste(shade, (0, 0), shade)
    dr = ImageDraw.Draw(im)
    _header(dr, d["period_label"].upper())
    dr.text((M, 130), d["title"].upper(), font=fit(dr, d["title"].upper(), 800, 96, W - 2 * M), fill=WHITE)
    dr.text((M, 236), d.get("subtitle", ""), font=bc(600, 30), fill=SOFT)
    rows = d["rows"][:10]
    top = 310; rh = min(92, (H - 120 - top) // max(1, len(rows)))
    for lab, x, right in (("FIGHTER", M + 230, False), ("PRICE", W - M - 300, True), ("7 DAYS", W - M - 24, True)):
        f = bc(700, 22); dr.text((x - dr.textlength(lab, font=f) if right else x, top - 34), lab, font=f, fill=MUTED)
    for i, r in enumerate(rows):
        y = top + i * rh; cy = y + (rh - 10) // 2
        dr.rounded_rectangle([M, y, W - M, y + rh - 10], 14, fill=PANEL, outline=LINE, width=2)
        tf = bc(800, 34); tw = dr.textlength(r["ticker"], font=tf)
        dr.rounded_rectangle([M + 24, cy - 24, M + 24 + tw + 28, cy + 24], 10, fill=(14, 60, 36))
        dr.text((M + 38, cy - 22), r["ticker"], font=tf, fill=GREEN)
        nf = fit(dr, r["name"], 700, 38, 360); dr.text((M + 230, cy - 24), r["name"], font=nf, fill=WHITE)
        v = money(r["new"]); vf = bc(700, 38); dr.text((W - M - 300 - dr.textlength(v, font=vf), cy - 24), v, font=vf, fill=WHITE)
        p = r["pct"]; c = GREEN if p >= 0 else RED; t = f"{'+' if p >= 0 else ''}{p:.1f}%"
        pf = bc(800, 38); dr.text((W - M - 24 - dr.textlength(t, font=pf), cy - 24), t, font=pf, fill=c)
    _footer(dr)
    _save(im, out)
