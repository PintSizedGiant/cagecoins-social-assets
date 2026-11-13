"""Cage Coins HEAD TO HEAD card, template T9 (13/11/2026).
Two fighters, red corner left and blue corner right, with a tale-of-the-tape table between them.
Shares background, fonts, flags and colours with T7 (cc_fighter.py). 1080x1350 PNG, no metadata."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import cc_fighter as F
from cc_fighter import W, H, M, WHITE, SOFT, MUTED, GREEN, RED, YELLOW, GREY, bc, fit, money, flag, DIV

C_RED, C_BLUE = (240, 82, 82), (86, 156, 255)

def rank_txt(rank, champ): return "CHAMP" if champ else ("NR" if rank in (None, 0, 99) else f"#{rank}")

def put_fighter(im, path, cx, top, bottom, max_w, mirror=False):
    if not (path and os.path.exists(path)): return
    ph = Image.open(path).convert("RGBA"); ph = ph.crop(ph.getchannel("A").getbbox())
    if mirror: ph = ph.transpose(Image.FLIP_LEFT_RIGHT)
    h = bottom - top; w = int(ph.width * h / ph.height)
    if w > max_w: w = max_w; h = int(ph.height * w / ph.width)
    ph = ph.resize((w, h), Image.LANCZOS)
    fade = Image.new("L", (w, h), 255); fp = fade.load(); band = int(h * 0.30)
    for y in range(h - band, h):
        v = int(255 * ((h - y) / band) ** 1.5)
        for x in range(w): fp[x, y] = v
    ph.putalpha(ImageChops.multiply(ph.getchannel("A"), fade))
    im.paste(ph, (int(cx - w / 2), bottom - h), ph)

def shade(im, y0=600, y1=900):
    band = Image.new("L", (1, H), 0); bp = band.load()
    for y in range(y0, H):
        bp[0, y] = int(205 * min(1.0, (y - y0) / (y1 - y0)))
    im.paste(Image.new("RGB", (W, H), (4, 9, 8)), (0, 0), band.resize((W, H)))

def form_chips(dr, x, y, results, align_right):
    cols = {"W": GREEN, "L": RED}
    size, gap = 34, 8
    total = len(results) * size + max(0, len(results) - 1) * gap
    x0 = x - total if align_right else x
    for i, r in enumerate(results):
        c = cols.get(r, YELLOW); xx = x0 + i * (size + gap)
        dr.rounded_rectangle([xx, y, xx + size, y + size], 7, fill=(c[0] // 5, c[1] // 5, c[2] // 5), outline=c, width=2)
        t = r if r in ("W", "L") else ("D" if r.upper().startswith("D") else "NC")
        tf = bc(800, 22 if len(t) == 1 else 17); tw = dr.textlength(t, font=tf)
        dr.text((xx + (size - tw) / 2, y + 5), t, font=tf, fill=c)

def card(d, photo_red, photo_blue, out):
    """d: event, event_date, weight_class, is_title, rounds, red{}, blue{}
       fighter: name ticker price prev_price country_code wins losses draws ko_wins sub_wins dec_wins rank champ ufc_w ufc_l streak form[]"""
    r, b = d["red"], d["blue"]
    im = F.background(sum(ord(c) for c in r["ticker"] + b["ticker"]))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([-260, 120, 520, 900], fill=C_RED + (40,)); gd.ellipse([560, 120, 1340, 900], fill=C_BLUE + (40,))
    glow = glow.filter(ImageFilter.GaussianBlur(120)); im.paste(glow, (0, 0), glow)
    put_fighter(im, photo_red, 280, 150, 690, 560)
    put_fighter(im, photo_blue, 800, 150, 690, 560)
    shade(im)
    dr = ImageDraw.Draw(im)
    # header
    dr.text((M, 40), "CAGECOINS", font=bc(800, 58), fill=WHITE)
    lab = f"{str(d['event']).split(':')[0].upper()} · {F.dmy_short(d['event_date'])}"
    lf = fit(dr, lab, 600, 28, 520); dr.text((W - M - dr.textlength(lab, font=lf), 54), lab, font=lf, fill=SOFT)
    t = "HEAD TO HEAD"; tf = bc(800, 34); dr.text(((W - dr.textlength(t, font=tf)) / 2, 112), t, font=tf, fill=WHITE)
    bl = f"{d['weight_class'].upper()}{' TITLE FIGHT' if d.get('is_title') else ''} · {d['rounds']} ROUNDS"
    bf = bc(600, 24); dr.text(((W - dr.textlength(bl, font=bf)) / 2, 150), bl, font=bf, fill=SOFT)
    # VS badge
    dr.ellipse([W // 2 - 52, 520, W // 2 + 52, 624], fill=(6, 12, 10), outline=WHITE, width=3)
    vf = bc(800, 52); dr.text((W // 2 - dr.textlength("VS", font=vf) / 2, 538), "VS", font=vf, fill=WHITE)
    # names, flags, price
    def side(f, x_edge, right, col):
        fl = flag(f.get("country_code"), 34)
        name = f["name"].upper(); nf = fit(dr, name, 800, 76, 420)
        nw = dr.textlength(name, font=nf)
        nx = x_edge - nw if right else x_edge
        dr.text((nx, 690), name, font=nf, fill=WHITE)
        corner = "BLUE CORNER" if right else "RED CORNER"; cf = bc(700, 22)
        cx = x_edge - dr.textlength(corner, font=cf) if right else x_edge
        dr.text((cx, 664), corner, font=cf, fill=col)
        if fl:
            fx = (cx - fl.width - 12) if right else (cx + dr.textlength(corner, font=cf) + 12)
            im.paste(fl, (int(fx), 660), fl)
        pt = money(f["price"]); pf = bc(800, 66); pw = dr.textlength(pt, font=pf)
        dr.text((x_edge - pw if right else x_edge, 776), pt, font=pf, fill=WHITE)
        sl = "SHARE PRICE"; sf = bc(600, 24); sw = dr.textlength(sl, font=sf)
        dr.text((x_edge - sw if right else x_edge, 856), sl, font=sf, fill=MUTED)
    side(r, M, False, C_RED); side(b, W - M, True, C_BLUE)
    # tale of the tape
    def rec(f): return f"{f['wins']}-{f['losses']}" + (f"-{f['draws']}" if f.get("draws") else "")
    def split(f): return "-" if None in (f.get("ko_wins"), f.get("sub_wins"), f.get("dec_wins")) else f"{f['ko_wins']} / {f['sub_wins']} / {f['dec_wins']}"
    rows = [("RANK", rank_txt(r.get("rank"), r.get("champ")), rank_txt(b.get("rank"), b.get("champ"))),
            ("PRO RECORD", rec(r), rec(b)),
            ("UFC RECORD", f"{r['ufc_w']}-{r['ufc_l']}", f"{b['ufc_w']}-{b['ufc_l']}"),
            ("KO / SUB / DEC", split(r), split(b)),
            ("WIN STREAK", f"W{r.get('streak') or 0}", f"W{b.get('streak') or 0}"),
            ("LAST 5", None, None)]
    y0, rh = 916, 56
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([M, y0 - 12, W - M, y0 + rh * len(rows) + 4], 18, fill=(6, 12, 10, 215), outline=(255, 255, 255, 30), width=2)
    im.paste(panel, (0, 0), panel); dr = ImageDraw.Draw(im)
    for i, (label, lv, rv) in enumerate(rows):
        y = y0 + i * rh
        if i: dr.line([(M + 20, y - 4), (W - M - 20, y - 4)], fill=(255, 255, 255, 18) if False else (30, 40, 36), width=1)
        lf2 = bc(700, 24); dr.text((W / 2 - dr.textlength(label, font=lf2) / 2, y + 12), label, font=lf2, fill=MUTED)
        if label == "LAST 5":
            form_chips(dr, M + 28, y + 6, r.get("form") or [], False)
            form_chips(dr, W - M - 28, y + 6, b.get("form") or [], True)
            continue
        vf2 = bc(800, 36)
        dr.text((M + 28, y + 4), lv, font=vf2, fill=WHITE)
        dr.text((W - M - 28 - dr.textlength(rv, font=vf2), y + 4), rv, font=vf2, fill=WHITE)
    # footer
    dr.text((M, H - 66), "cagecoins.com", font=bc(700, 34), fill=GREEN)
    d1 = "(NO FIGHTER AFFILIATION)"; d2 = "Fantasy money only · Not affiliated with the UFC"
    dr.text((W - M - dr.textlength(d1, font=bc(700, 24)), H - 74), d1, font=bc(700, 24), fill=SOFT)
    dr.text((W - M - dr.textlength(d2, font=bc(600, 22)), H - 44), d2, font=bc(600, 22), fill=MUTED)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.save(out, "PNG", optimize=True)


# ---------------------------------------------------------------- T10: head to head after the fight
def card_after(d, photo_red, photo_blue, out):
    """d: event, event_date, weight_class, is_title, winner ('red'|'blue'), method, round, time, red{}, blue{}
       fighter: name ticker country_code old new (event price move; old/new may be None when not recorded)"""
    r, b = d["red"], d["blue"]; red_won = d["winner"] == "red"
    m = (d.get("method") or "").upper()
    meth = "KO/TKO" if (m.startswith("KO") or "TKO" in m) else "SUBMISSION" if m.startswith("SUB") else "DECISION" if m.startswith("DEC") else (d.get("method") or "").upper()
    im = F.background(sum(ord(c) for c in r["ticker"] + b["ticker"]) + 3)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([-260, 120, 520, 900], fill=(GREEN if red_won else RED) + (44,)); gd.ellipse([560, 120, 1340, 900], fill=(RED if red_won else GREEN) + (44,))
    glow = glow.filter(ImageFilter.GaussianBlur(120)); im.paste(glow, (0, 0), glow)
    def dim(path):   # loser's image greyed and darkened
        if not (path and os.path.exists(path)): return path
        ph = Image.open(path).convert("RGBA"); a = ph.getchannel("A")
        g = ph.convert("L").convert("RGB").point(lambda v: int(v * 0.62)); g.putalpha(a)
        out_p = f"/tmp/dim_{os.path.basename(path)}"; g.save(out_p); return out_p
    put_fighter(im, photo_red if red_won else dim(photo_red), 280, 150, 690, 560)
    put_fighter(im, dim(photo_blue) if red_won else photo_blue, 800, 150, 690, 560)
    shade(im)
    dr = ImageDraw.Draw(im)
    dr.text((M, 40), "CAGECOINS", font=bc(800, 58), fill=WHITE)
    lab = f"{str(d['event']).split(':')[0].upper()} · {F.dmy_short(d['event_date'])}"
    lf = fit(dr, lab, 600, 28, 520); dr.text((W - M - dr.textlength(lab, font=lf), 54), lab, font=lf, fill=SOFT)
    t = "HEAD TO HEAD · RESULT"; tf = bc(800, 34); dr.text(((W - dr.textlength(t, font=tf)) / 2, 112), t, font=tf, fill=WHITE)
    bl = f"{d['weight_class'].upper()}{' TITLE FIGHT' if d.get('is_title') else ''}"
    bf = bc(600, 24); dr.text(((W - dr.textlength(bl, font=bf)) / 2, 150), bl, font=bf, fill=SOFT)
    dr.ellipse([W // 2 - 52, 520, W // 2 + 52, 624], fill=(6, 12, 10), outline=WHITE, width=3)
    vf = bc(800, 52); dr.text((W // 2 - dr.textlength("VS", font=vf) / 2, 538), "VS", font=vf, fill=WHITE)
    def side(f, x_edge, right, won):
        col = GREEN if won else RED
        chip = "WINNER" if won else "LOSER"; cf = bc(800, 30); cw = dr.textlength(chip, font=cf)
        cx = x_edge - cw - 32 if right else x_edge
        dr.rounded_rectangle([cx, 648, cx + cw + 32, 692], 10, fill=col); dr.text((cx + 16, 652), chip, font=cf, fill=(8, 14, 12))
        fl = flag(f.get("country_code"), 34)
        if fl: im.paste(fl, (int(cx - fl.width - 12) if right else int(cx + cw + 44), 653), fl)
        name = f["name"].upper(); nf = fit(dr, name, 800, 76, 420); nw = dr.textlength(name, font=nf)
        dr.text((x_edge - nw if right else x_edge, 700), name, font=nf, fill=WHITE if won else SOFT)
        if f.get("old") is not None and f.get("new") is not None:
            up = f["new"] >= f["old"]; pc = GREEN if up else RED
            chg = f["new"] - f["old"]; pct = chg / f["old"] * 100 if f["old"] else 0
            pt = money(f["new"]); pf = bc(800, 66); pw = dr.textlength(pt, font=pf)
            dr.text((x_edge - pw if right else x_edge, 776), pt, font=pf, fill=WHITE)
            ct = f"{'+' if up else '-'}{abs(pct):.2f}%   from {money(f['old'])}"; cf2 = bc(700, 28); cw2 = dr.textlength(ct, font=cf2)
            tx = (x_edge - cw2) if right else (x_edge + 30); tri_x = (tx - 30) if right else x_edge; ty = 856
            tri = [(tri_x, ty + 24), (tri_x + 22, ty + 24), (tri_x + 11, ty + 5)] if up else [(tri_x, ty + 5), (tri_x + 22, ty + 5), (tri_x + 11, ty + 24)]
            dr.polygon(tri, fill=pc); dr.text((tx, ty - 2), ct, font=cf2, fill=pc)
        else:
            nt = "no price move recorded"; nf2 = bc(600, 28)
            dr.text((x_edge - dr.textlength(nt, font=nf2) if right else x_edge, 790), nt, font=nf2, fill=MUTED)
    side(r, M, False, red_won); side(b, W - M, True, not red_won)
    win, lose = (r, b) if red_won else (b, r)
    rows = [("RESULT", "WIN" if red_won else "LOSS", "LOSS" if red_won else "WIN"),
            ("METHOD", meth, meth)]
    if d.get("round"): rows.append(("ROUND", f"R{d['round']} · {d.get('time') or ''}".strip(" ·"), f"R{d['round']} · {d.get('time') or ''}".strip(" ·")))
    def pr(f, k): return money(f[k]) if f.get(k) is not None else "-"
    def ch(f): return f"{(f['new'] - f['old']) / f['old'] * 100:+.2f}%" if f.get("old") and f.get("new") is not None else "-"
    rows += [("PRICE BEFORE", pr(r, "old"), pr(b, "old")), ("PRICE AFTER", pr(r, "new"), pr(b, "new")), ("CHANGE", ch(r), ch(b))]
    y0, rh = 924, 52
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([M, y0 - 12, W - M, y0 + rh * len(rows) + 4], 18, fill=(6, 12, 10, 215), outline=(255, 255, 255, 30), width=2)
    im.paste(panel, (0, 0), panel); dr = ImageDraw.Draw(im)
    for i, (label, lv, rv) in enumerate(rows):
        y = y0 + i * rh
        if i: dr.line([(M + 20, y - 4), (W - M - 20, y - 4)], fill=(30, 40, 36), width=1)
        lf2 = bc(700, 24); dr.text((W / 2 - dr.textlength(label, font=lf2) / 2, y + 11), label, font=lf2, fill=MUTED)
        def colr(v):
            if label == "RESULT": return GREEN if v == "WIN" else RED
            if label == "CHANGE" and v != "-": return GREEN if v.startswith("+") else RED
            return WHITE
        vf2 = bc(800, 34)
        dr.text((M + 28, y + 4), lv, font=vf2, fill=colr(lv))
        dr.text((W - M - 28 - dr.textlength(rv, font=vf2), y + 4), rv, font=vf2, fill=colr(rv))
    dr.text((M, H - 66), "cagecoins.com", font=bc(700, 34), fill=GREEN)
    d1 = "(NO FIGHTER AFFILIATION)"; d2 = "Fantasy money only · Not affiliated with the UFC"
    dr.text((W - M - dr.textlength(d1, font=bc(700, 24)), H - 74), d1, font=bc(700, 24), fill=SOFT)
    dr.text((W - M - dr.textlength(d2, font=bc(600, 22)), H - 44), d2, font=bc(600, 22), fill=MUTED)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.save(out, "PNG", optimize=True)
