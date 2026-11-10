"""Cage Coins social card renderer. Plain drawing code: no AI image tools, no metadata written.
Templates: T1 mover (text), T1p mover (photo), T2 matchup, T3a/T3b/T3c recap carousel, T4 movers, T5 prospect, T6 top trader.
All cards are 1080x1350. Every number shown comes from the dict passed in."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
def _font(name, size): return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)
def inter(w, s): return _font(f"Inter-{w}.otf", s)
def mono(s, bold=False): return _font("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf", s)

W, H, M = 1080, 1350, 64
BLACK, PANEL, LINE = (0, 0, 0), (13, 16, 24), (38, 44, 58)
GOLD, WHITE, MUTED, SOFT = (245, 176, 49), (236, 239, 244), (140, 148, 163), (200, 205, 215)
GREEN, RED, C_RED, C_BLUE = (52, 211, 120), (240, 82, 82), (240, 82, 82), (86, 156, 255)
FOOT = "Fantasy money only · Not affiliated with the UFC"
PHOTO_BOX = (500, 130, 1080, 950)

def fit(dr, text, maker, start, max_w, floor=18):
    s = start
    while s > floor and dr.textlength(text, font=maker(s)) > max_w: s -= 2
    return maker(s)
def money(v): return f"${v:,.2f}"
def pct(old, new): return (new - old) / old * 100
def rank_txt(rank, champ): return "C" if champ else ("NR" if rank in (None, 0, 99) else f"#{rank}")

def base(label="", credit=""):
    im = Image.new("RGB", (W, H), BLACK); dr = ImageDraw.Draw(im)
    dr.text((M, 56), "CAGE", font=mono(46, True), fill=GOLD)
    dr.text((M + dr.textlength("CAGE ", font=mono(46, True)), 56), "COINS", font=mono(46, True), fill=WHITE)
    if label:
        f = fit(dr, label, lambda s: mono(s), 24, 560); dr.text((W - M - dr.textlength(label, font=f), 72), label, font=f, fill=MUTED)
    dr.text((M, H - 54), "cagecoins.com", font=mono(24, True), fill=GOLD)
    ft = " · ".join(x for x in [credit, FOOT] if x); ff = fit(dr, ft, lambda s: inter("Regular", s), 18, 640, 12)
    dr.text((W - M - dr.textlength(ft, font=ff), H - 49), ft, font=ff, fill=MUTED)
    return im, dr
def rule(dr): dr.line([(M, 136), (W - M, 136)], fill=LINE, width=2)

def chip(dr, x, y, text, size=32, pad=15):
    f = mono(size, True); w = dr.textlength(text, font=f)
    dr.rounded_rectangle([x, y, x + w + 2 * pad, y + size + 20], 9, fill=GOLD)
    dr.text((x + pad, y + 7), text, font=f, fill=BLACK); return x + w + 2 * pad
def pct_chip(dr, right, y, p, size=40):
    col = GREEN if p >= 0 else RED; t = f"{'▲' if p >= 0 else '▼'} {abs(p):.1f}%"
    f = mono(size, True); w = dr.textlength(t, font=f)
    dr.rounded_rectangle([right - w - 36, y, right, y + size + 28], 12, fill=(col[0]//7, col[1]//7, col[2]//7), outline=col, width=2)
    dr.text((right - w - 18, y + 11), t, font=f, fill=col)
def save(im, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True); im.save(out, "PNG", optimize=True)

# ---- T1 mover, text only.  d: label ticker division name old new result_head result_sub
def t1(d, out):
    im, dr = base(d.get("label", "")); rule(dr)
    x = chip(dr, M, 210, d["ticker"], size=44, pad=20)
    dr.text((x + 24, 228), d["division"].upper(), font=mono(28), fill=MUTED)
    dr.text((M, 316), d["name"], font=fit(dr, d["name"], lambda s: inter("Bold", s), 104, W - 2 * M), fill=WHITE)
    dr.rounded_rectangle([M, 500, W - M, 980], 24, fill=PANEL, outline=LINE, width=2)
    dr.text((M + 48, 540), "PRICE BEFORE", font=mono(26), fill=MUTED)
    dr.text((M + 48, 584), money(d["old"]), font=mono(72), fill=MUTED)
    dr.text((M + 48, 716), "PRICE NOW", font=mono(26), fill=MUTED)
    nt = money(d["new"]); dr.text((M + 48, 760), nt, font=fit(dr, nt, lambda s: mono(s, True), 150, W - 2 * M - 96), fill=WHITE)
    pct_chip(dr, W - M - 48, 560, pct(d["old"], d["new"]), size=64)
    dr.text((M, 1030), d["result_head"], font=fit(dr, d["result_head"], lambda s: inter("SemiBold", s), 48, W - 2 * M), fill=WHITE)
    dr.text((M, 1100), d["result_sub"], font=inter("Regular", 36), fill=MUTED)
    save(im, out)

# ---- T1p mover with cut-out photo. Same dict plus optional rank, country, credit.
def t1p(d, photo_path, out):
    x0, y0, x1, y1 = PHOTO_BOX; bw, bh = x1 - x0, y1 - y0
    im, dr = base("", d.get("credit", ""))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([x0 - 40, y0 + 40, x1 + 80, y1 - 20], fill=(245, 176, 49, 38))
    glow = glow.filter(ImageFilter.GaussianBlur(110)); im.paste(glow, (0, 0), glow)
    ph = Image.open(photo_path).convert("RGBA")
    ph = ph.resize((max(1, int(ph.width * bh / ph.height)), bh), Image.LANCZOS)
    if ph.width > bw:
        off = (ph.width - bw) // 2; ph = ph.crop((off, 0, off + bw, bh))
    layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); layer.paste(ph, ((bw - ph.width) // 2, 0), ph)
    mask = Image.new("L", (bw, bh), 255); mp = mask.load()
    for y in range(bh):
        fy = min(1.0, (bh - y) / 150)
        for x in range(bw): mp[x, y] = int(255 * fy * min(1.0, (x + 1) / 60))
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask)); im.paste(layer, (x0, y0), layer)
    dr = ImageDraw.Draw(im); colw = x0 - M - 20
    p = pct(d["old"], d["new"]); col = GREEN if p >= 0 else RED; pt = f"{'▲' if p >= 0 else '▼'} {abs(p):.1f}%"
    f = fit(dr, pt, lambda s: mono(s, True), 84, colw - 56); pw = dr.textlength(pt, font=f)
    dr.rounded_rectangle([M, 260, M + pw + 56, 400], 18, fill=(col[0]//7, col[1]//7, col[2]//7), outline=col, width=3)
    dr.text((M + 28, 330 - f.size // 2 - 6), pt, font=f, fill=col)
    dr.text((M, 490), "NOW", font=mono(26), fill=MUTED)
    nt = money(d["new"]); dr.text((M, 526), nt, font=fit(dr, nt, lambda s: mono(s, True), 104, colw), fill=WHITE)
    dr.text((M, 710), "BEFORE", font=mono(26), fill=MUTED)
    ot = money(d["old"]); dr.text((M, 746), ot, font=fit(dr, ot, lambda s: mono(s), 64, colw), fill=MUTED)
    by = y1 + 28; x = chip(dr, M, by, d["ticker"])
    meta = "   ".join(t for t in [d["division"].upper(), d.get("rank", ""), d.get("country", "").upper()] if t)
    dr.text((x + 22, by + 12), meta, font=mono(25), fill=SOFT)
    dr.text((M, by + 62), d["name"], font=fit(dr, d["name"], lambda s: inter("Bold", s), 88, W - 2 * M), fill=WHITE)
    ry = by + 62 + 124; dr.line([(M, ry + 4), (M, ry + 76)], fill=GOLD, width=5)
    dr.text((M + 22, ry), d["result_head"], font=fit(dr, d["result_head"], lambda s: inter("SemiBold", s), 36, W - 2 * M - 22), fill=WHITE)
    dr.text((M + 22, ry + 46), d["result_sub"], font=inter("Regular", 28), fill=(170, 177, 190))
    save(im, out)

# ---- T2 matchup.  d: event_label kicker bout_line red{} blue{}  (fighter: name ticker price rank champ w l country)
def t2(d, out):
    im, dr = base(d["event_label"]); rule(dr)
    dr.text((M, 176), d["kicker"].upper(), font=mono(28, True), fill=GOLD)
    dr.text((M, 220), d["bout_line"].upper(), font=fit(dr, d["bout_line"].upper(), lambda s: mono(s), 26, W - 2 * M), fill=SOFT)
    def corner(y, side, f):
        col = C_RED if side == "RED" else C_BLUE
        dr.rounded_rectangle([M, y, W - M, y + 400], 22, fill=PANEL, outline=LINE, width=2)
        dr.rectangle([M, y + 22, M + 7, y + 378], fill=col)
        dr.text((M + 40, y + 34), f"{side} CORNER", font=mono(22, True), fill=col)
        x = chip(dr, M + 40, y + 78, f["ticker"])
        meta = "   ".join([rank_txt(f["rank"], f["champ"]), f"UFC {f['w']}-{f['l']}", (f.get("country") or "").upper()])
        dr.text((x + 22, y + 90), meta, font=fit(dr, meta, lambda s: mono(s), 25, W - M - 40 - x - 22), fill=SOFT)
        dr.text((M + 40, y + 150), f["name"], font=fit(dr, f["name"], lambda s: inter("Bold", s), 84, W - 2 * M - 80), fill=WHITE)
        dr.text((M + 40, y + 268), "PRICE", font=mono(22), fill=MUTED)
        dr.text((M + 40, y + 296), money(f["price"]), font=mono(76, True), fill=WHITE)
    corner(290, "RED", d["red"]); corner(750, "BLUE", d["blue"])
    vf = mono(34, True); dr.ellipse([W//2 - 44, 676, W//2 + 44, 764], fill=BLACK, outline=GOLD, width=3)
    dr.text((W//2 - dr.textlength("VS", font=vf)/2, 700), "VS", font=vf, fill=GOLD)
    hi, lo = sorted([d["red"], d["blue"]], key=lambda f: -f["price"])
    note = f"{hi['ticker']} trades at {hi['price']/lo['price']:.1f}x the price of {lo['ticker']}"
    dr.text((M, 1182), note, font=fit(dr, note, lambda s: inter("SemiBold", s), 34, W - 2 * M), fill=SOFT)
    save(im, out)

# ---- T3a recap cover.  d: date event_lines[] venue stats[(k,v)x3]
def t3a(d, out):
    im, dr = base(d["date"]); rule(dr)
    dr.text((M, 300), "RESULTS", font=mono(34, True), fill=GOLD)
    dr.text((M, 356), "How the market moved", font=inter("Bold", 84), fill=WHITE)
    y = 520
    for line in d["event_lines"]:
        dr.text((M, y), line, font=fit(dr, line, lambda s: inter("SemiBold", s), 52, W - 2 * M), fill=SOFT); y += 70
    dr.text((M, y + 20), d["venue"], font=fit(dr, d["venue"], lambda s: inter("Regular", s), 30, W - 2 * M), fill=MUTED)
    dr.rounded_rectangle([M, 900, W - M, 1110], 22, fill=PANEL, outline=LINE, width=2)
    cw = (W - 2 * M - 88) // len(d["stats"])
    for i, (k, v) in enumerate(d["stats"]):
        x = M + 44 + i * cw
        dr.text((x, 936), k, font=mono(22), fill=MUTED); dr.text((x, 972), v, font=fit(dr, v, lambda s: mono(s, True), 64, cw - 20), fill=WHITE)
    dr.text((M, 1170), "Swipe for every fight  →", font=mono(28, True), fill=GOLD)
    save(im, out)

# ---- T3b recap fight slide.  d: event_short tag weight_class winner{} loser{} method_line time_line
#      fighter: name ticker, and either old+new or price (when no move was recorded)
def t3b(d, out):
    im, dr = base(d["event_short"]); rule(dr)
    dr.text((M, 176), d["tag"].upper(), font=mono(28, True), fill=GOLD)
    dr.text((M, 220), d["weight_class"].upper(), font=mono(26), fill=SOFT)
    def row(y, res, f):
        col = GREEN if res == "W" else RED
        dr.rounded_rectangle([M, y, W - M, y + 380], 22, fill=PANEL, outline=LINE, width=2)
        dr.rounded_rectangle([M + 40, y + 36, M + 104, y + 100], 12, fill=(col[0]//6, col[1]//6, col[2]//6), outline=col, width=2)
        dr.text((M + 58, y + 46), res, font=mono(38, True), fill=col)
        if f.get("ticker"): chip(dr, M + 128, y + 42, f["ticker"])
        dr.text((M + 40, y + 124), f["name"], font=fit(dr, f["name"], lambda s: inter("Bold", s), 72, W - 2 * M - 80), fill=WHITE)
        if f.get("old") is not None and f.get("new") is not None:
            dr.text((M + 40, y + 232), "BEFORE", font=mono(22), fill=MUTED); dr.text((M + 40, y + 262), money(f["old"]), font=mono(44), fill=MUTED)
            dr.text((M + 330, y + 232), "NOW", font=mono(22), fill=MUTED); dr.text((M + 330, y + 252), money(f["new"]), font=mono(60, True), fill=WHITE)
            pct_chip(dr, W - M - 40, y + 252, pct(f["old"], f["new"]))
        elif f.get("price") is not None:
            dr.text((M + 40, y + 232), "PRICE", font=mono(22), fill=MUTED); dr.text((M + 40, y + 252), money(f["price"]), font=mono(60, True), fill=WHITE)
            dr.text((M + 330, y + 276), "no price move recorded", font=inter("Regular", 26), fill=MUTED)
        else:
            dr.text((M + 40, y + 262), "not listed on Cage Coins", font=inter("Regular", 30), fill=MUTED)
    row(290, "W", d["winner"]); row(700, "L", d["loser"])
    dr.line([(M, 1128), (M, 1196)], fill=GOLD, width=5)
    dr.text((M + 22, 1122), d["method_line"], font=fit(dr, d["method_line"], lambda s: inter("SemiBold", s), 36, W - 2 * M - 22), fill=WHITE)
    dr.text((M + 22, 1168), d["time_line"], font=inter("Regular", 28), fill=SOFT)
    save(im, out)

# ---- T3c recap closing slide.  d: start_cash next_line
def t3c(d, out):
    im, dr = base(); rule(dr)
    dr.text((M, 380), "Prices move on", font=inter("Bold", 92), fill=WHITE)
    dr.text((M, 490), "fight results.", font=inter("Bold", 92), fill=GOLD)
    dr.text((M, 660), "Trade UFC fighters like stocks.", font=inter("SemiBold", 44), fill=SOFT)
    dr.text((M, 724), f"Start with {d['start_cash']} of fantasy cash.", font=inter("SemiBold", 44), fill=SOFT)
    dr.rounded_rectangle([M, 880, W - M, 1010], 20, fill=GOLD)
    t = "cagecoins.com"; f = mono(60, True); dr.text(((W - dr.textlength(t, font=f)) / 2, 912), t, font=f, fill=BLACK)
    if d.get("next_line"): dr.text((M, 1070), d["next_line"], font=fit(dr, d["next_line"], lambda s: mono(s), 28, W - 2 * M), fill=MUTED)
    save(im, out)

# ---- T4 movers.  d: label title risers[] fallers[]  (row: ticker name old new), max 5 each
def t4(d, out):
    im, dr = base(d["label"]); rule(dr)
    dr.text((M, 176), d["title"], font=inter("Bold", 68), fill=WHITE)
    def block(y, head, col, rows):
        if not rows: return y
        dr.text((M, y), head, font=mono(26, True), fill=col); y += 46
        for r in rows[:5]:
            dr.rounded_rectangle([M, y, W - M, y + 70], 14, fill=PANEL, outline=LINE, width=1)
            chip(dr, M + 20, y + 11, r["ticker"], size=28, pad=12)
            dr.text((M + 190, y + 17), r["name"], font=fit(dr, r["name"], lambda s: inter("SemiBold", s), 32, 380), fill=WHITE)
            pt = money(r["new"]); pf = mono(30, True); dr.text((W - M - 250 - dr.textlength(pt, font=pf), y + 19), pt, font=pf, fill=WHITE)
            p = pct(r["old"], r["new"]); t = f"{'▲' if p >= 0 else '▼'} {abs(p):.1f}%"; tf = mono(30, True)
            dr.text((W - M - 24 - dr.textlength(t, font=tf), y + 19), t, font=tf, fill=GREEN if p >= 0 else RED)
            y += 82
        return y + 34
    y = block(290, "BIGGEST RISERS", GREEN, d["risers"]); block(y, "BIGGEST FALLERS", RED, d["fallers"])
    save(im, out)

# ---- T5 prospect.  d: ticker name division country price old stats[(k,v)x3] last_head last_sub
def t5(d, out):
    im, dr = base("PROSPECT WATCH"); rule(dr)
    x = chip(dr, M, 200, d["ticker"], size=40, pad=18)
    dr.text((x + 24, 216), "   ".join([d["division"].upper(), (d.get("country") or "").upper()]), font=mono(26), fill=SOFT)
    dr.text((M, 290), d["name"], font=fit(dr, d["name"], lambda s: inter("Bold", s), 110, W - 2 * M), fill=WHITE)
    dr.rounded_rectangle([M, 470, W - M, 760], 22, fill=PANEL, outline=LINE, width=2)
    dr.text((M + 44, 506), "PRICE NOW", font=mono(24), fill=MUTED)
    nt = money(d["price"]); dr.text((M + 44, 544), nt, font=fit(dr, nt, lambda s: mono(s, True), 132, 600), fill=WHITE)
    if d.get("old") is not None: pct_chip(dr, W - M - 44, 520, pct(d["old"], d["price"]), size=44)
    cw = (W - 2 * M - 48) // 3
    for i, (k, v) in enumerate(d["stats"]):
        x0 = M + i * (cw + 24)
        dr.rounded_rectangle([x0, 800, x0 + cw, 980], 18, fill=PANEL, outline=LINE, width=2)
        dr.text((x0 + 28, 828), k, font=mono(22), fill=MUTED)
        dr.text((x0 + 28, 866), v, font=fit(dr, v, lambda s: mono(s, True), 64, cw - 56), fill=WHITE)
    dr.line([(M, 1046), (M, 1150)], fill=GOLD, width=5)
    dr.text((M + 22, 1040), d["last_head"], font=fit(dr, d["last_head"], lambda s: inter("SemiBold", s), 38, W - 2 * M - 22), fill=WHITE)
    dr.text((M + 22, 1092), d["last_sub"], font=fit(dr, d["last_sub"], lambda s: inter("Regular", s), 30, W - 2 * M - 22), fill=SOFT)
    save(im, out)

# ---- T6 top trader.  d: period_label title username return_label return_pct net_worth start_cash
def t6(d, out):
    im, dr = base(d["period_label"]); rule(dr)
    dr.text((M, 250), d["title"].upper(), font=mono(32, True), fill=GOLD)
    dr.text((M, 320), d["username"], font=fit(dr, d["username"], lambda s: inter("Bold", s), 150, W - 2 * M), fill=WHITE)
    dr.rounded_rectangle([M, 560, W - M, 880], 22, fill=PANEL, outline=LINE, width=2)
    dr.text((M + 44, 596), d["return_label"], font=mono(24), fill=MUTED)
    col = GREEN if d["return_pct"] >= 0 else RED; rt = f"{'+' if d['return_pct'] >= 0 else '-'}{abs(d['return_pct']):.2f}%"
    dr.text((M + 44, 640), rt, font=fit(dr, rt, lambda s: mono(s, True), 150, W - 2 * M - 88), fill=col)
    dr.text((M, 940), "ACCOUNT VALUE", font=mono(24), fill=MUTED)
    dr.text((M, 976), money(d["net_worth"]), font=mono(72, True), fill=WHITE)
    dr.text((M, 1130), f"Everyone starts with {d['start_cash']} of fantasy cash.", font=inter("SemiBold", 34), fill=SOFT)
    save(im, out)
