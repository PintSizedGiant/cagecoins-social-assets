"""Cage Coins fighter card, template T7 (after Oli's reference, 13/11/2026).
Candlestick background drawn by code, fighter cut-out from photos/TICKER.png, live price panel,
and a five-box fight row (next bout in grey on the left when booked). 1080x1350 PNG, no metadata."""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
FLAG_DIR = os.path.join(HERE, "flags")

W, H, M = 1080, 1350, 56
BG_TOP, BG_BOT = (8, 20, 16), (3, 8, 7)
WHITE, SOFT, MUTED = (240, 244, 242), (196, 206, 201), (128, 143, 136)
GREEN, RED, YELLOW, GREY = (52, 211, 120), (240, 82, 82), (250, 204, 21), (150, 160, 172)
DIV = {"Heavyweight": "HW", "Light Heavyweight": "LHW", "Middleweight": "MW", "Welterweight": "WW", "Lightweight": "LW",
       "Featherweight": "FW", "Bantamweight": "BW", "Flyweight": "FLW", "Women's Strawweight": "W-SW",
       "Women's Flyweight": "W-FLW", "Women's Bantamweight": "W-BW", "Women's Featherweight": "W-FW"}

def bc(w, s): return ImageFont.truetype(os.path.join(FONT_DIR, f"BarlowCondensed-{w}.ttf"), s)
_BARLOW = None
def barlow_ok(text):
    """Barlow Condensed only covers basic Latin. Names like Uroš Medić or Cyrillic usernames need Inter."""
    global _BARLOW
    if _BARLOW is None:
        from fontTools.ttLib import TTFont
        _BARLOW = set(TTFont(os.path.join(FONT_DIR, "BarlowCondensed-800.ttf")).getBestCmap())
    return all(ord(c) in _BARLOW for c in str(text))
def _inter(w, s): return ImageFont.truetype(os.path.join(FONT_DIR, "Inter-Bold.otf" if w >= 700 else "Inter-SemiBold.otf"), s)
def fit(dr, text, w, start, max_w, floor=16):
    face = bc if barlow_ok(text) else _inter
    if face is _inter: start = int(start * 0.82)
    s = start
    while s > floor and dr.textlength(text, font=face(w, s)) > max_w: s -= 2
    return face(w, s)
def money(v): return f"${v:,.2f}"
def dmy_short(iso): y, m, d = str(iso)[:10].split("-"); return f"{d}/{m}/{y[2:]}"

def background(seed, line_col=(74, 222, 128)):
    im = Image.new("RGB", (W, H)); px = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H; px.line([(0, y), (W, y)], fill=tuple(int(BG_TOP[i] * (1 - t) + BG_BOT[i] * t) for i in range(3)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    for x in range(0, W, 90): dr.line([(x, 110), (x, 980)], fill=(255, 255, 255, 10))
    for y in range(110, 980, 90): dr.line([(0, y), (W, y)], fill=(255, 255, 255, 10))
    rnd = random.Random(seed)
    n, cw, gap = 46, 14, 9.5
    lo_y, hi_y = 900, 170
    level = 0.12; closes = []
    for i in range(n):
        o = level; level = min(0.98, max(0.04, level + rnd.uniform(-0.035, 0.06))); c = level
        hi, lo = max(o, c) + rnd.uniform(0, 0.03), min(o, c) - rnd.uniform(0, 0.03)
        x = 18 + i * (cw + gap); Y = lambda v: lo_y - v * (lo_y - hi_y)
        col = (34, 197, 94, 150) if c >= o else (239, 68, 68, 140)
        dr.line([(x + cw / 2, Y(hi)), (x + cw / 2, Y(lo))], fill=col, width=2)
        dr.rectangle([x, Y(max(o, c)), x + cw, max(Y(min(o, c)), Y(max(o, c)) + 3)], fill=col)
        closes.append((x + cw / 2, Y(c)))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(line)
    pts = [(x, y - 60) for x, y in closes[n // 3:]]
    ld.line(pts, fill=tuple(line_col) + (255,), width=5, joint="curve")
    glow = line.filter(ImageFilter.GaussianBlur(10))
    im.paste(layer, (0, 0), layer); im.paste(glow, (0, 0), glow); im.paste(line, (0, 0), line)
    vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse([220, 120, 820, 980], fill=120)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    im.paste(Image.new("RGB", (W, H), BG_BOT), (0, 0), vig)
    return im

def place_fighter(im, path):
    box_top, box_bot, cx = 70, 960, 500
    ph = Image.open(path).convert("RGBA")
    bbox = ph.getchannel("A").getbbox(); ph = ph.crop(bbox)
    h = box_bot - box_top; w = int(ph.width * h / ph.height)
    if w > 900: w = 900; h = int(ph.height * w / ph.width)
    ph = ph.resize((w, h), Image.LANCZOS)
    fade = Image.new("L", (w, h), 255); fp = fade.load(); band = int(h * 0.26)
    for y in range(h - band, h):
        v = int(255 * ((h - y) / band) ** 1.6)
        for x in range(w): fp[x, y] = v
    ph.putalpha(ImageChops.multiply(ph.getchannel("A"), fade))
    im.paste(ph, (cx - w // 2, box_bot - h), ph)

def flag(code, height):
    import cairosvg
    p = os.path.join(FLAG_DIR, f"{(code or '').lower()}.svg")
    if not code or not os.path.exists(p): return None
    out = os.path.join("/tmp", f"flag_{code.lower()}_{height}.png")
    if not os.path.exists(out): cairosvg.svg2png(url=p, write_to=out, output_height=height)
    return Image.open(out).convert("RGBA")

def fight_box(dr, x, y, w, h, kind, name, line1, line2):
    col = {"W": GREEN, "L": RED, "NC": YELLOW, "D": YELLOW, "NEXT": GREY}[kind]
    label = {"W": "WIN", "L": "LOSS", "NC": "NO CONTEST", "D": "DRAW", "NEXT": "NEXT"}[kind]
    dr.rounded_rectangle([x, y, x + w, y + h], 16, fill=(col[0] // 7, col[1] // 7, col[2] // 7), outline=col, width=3)
    dr.rectangle([x + 3, y + 3, x + w - 3, y + 8], fill=col)
    f = fit(dr, label, 800, 30, w - 36); dr.text((x + 18, y + 22), label, font=f, fill=col)
    parts = name.split(" ", 1)
    first, last = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])
    if first: dr.text((x + 18, y + 64), first, font=fit(dr, first, 600, 26, w - 36), fill=SOFT)
    dr.text((x + 18, y + 92), last.upper(), font=fit(dr, last.upper(), 800, 38, w - 36), fill=WHITE)
    dr.text((x + 18, y + 146), line1, font=fit(dr, line1, 700, 26, w - 36), fill=col if kind != "NEXT" else SOFT)
    dr.text((x + 18, y + 178), line2, font=fit(dr, line2, 600, 24, w - 36), fill=MUTED)

def card(f, photo_path, out):
    """f: name ticker price prev_price country_code division wins losses draws ko_wins sub_wins dec_wins last_fights next_bout"""
    seed = sum(ord(c) for c in f["ticker"])
    im = background(seed)
    if photo_path and os.path.exists(photo_path): place_fighter(im, photo_path)
    dr = ImageDraw.Draw(im)
    # header
    dr.text((M, 40), "CAGECOINS", font=bc(800, 58), fill=WHITE)
    t = "FIGHTER STOCKS"; tf = bc(600, 28); tw = dr.textlength(t, font=tf)
    dr.text((W - M - tw, 54), t, font=tf, fill=SOFT); dr.ellipse([W - M - tw - 26, 64, W - M - tw - 12, 78], fill=GREEN)
    # price panel (right)
    up = f["price"] >= f["prev_price"]; col = GREEN if up else RED
    chg = f["price"] - f["prev_price"]; pct = chg / f["prev_price"] * 100 if f["prev_price"] else 0
    px0, py0, px1, py1 = 690, 748, W - M, 972
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([px0, py0, px1, py1], 22, fill=(col[0] // 6, col[1] // 6, col[2] // 6, 225), outline=col + (255,), width=3)
    im.paste(panel, (0, 0), panel); dr = ImageDraw.Draw(im)
    dr.text((px0 + 28, py0 + 22), "SHARE PRICE", font=bc(600, 28), fill=SOFT)
    pt = money(f["price"]); dr.text((px0 + 26, py0 + 52), pt, font=fit(dr, pt, 800, 96, px1 - px0 - 52), fill=WHITE)
    ty = py0 + 166; tri = [(px0 + 28, ty + 26), (px0 + 52, ty + 26), (px0 + 40, ty + 6)] if up else [(px0 + 28, ty + 6), (px0 + 52, ty + 6), (px0 + 40, ty + 26)]
    dr.polygon(tri, fill=col)
    ct = f"{'+' if up else '-'}{abs(pct):.2f}%    {'+' if up else '-'}{money(abs(chg))}"
    dr.text((px0 + 64, ty - 4), ct, font=fit(dr, ct, 700, 36, px1 - px0 - 92), fill=col)
    # name block (left)
    fl = flag(f.get("country_code"), 58); nx = M
    if fl: im.paste(fl, (M, 818), fl); dr.rectangle([M, 818, M + fl.width - 1, 818 + fl.height - 1], outline=(255, 255, 255, 60)); nx = M + fl.width + 20
    name = f["name"].upper(); nf = fit(dr, name, 800, 118, px0 - 24 - nx)
    dr.text((nx, 846 - nf.size * 0.62), name, font=nf, fill=WHITE)
    rec = f"{f['wins']}-{f['losses']}" + (f"-{f['draws']}" if f.get("draws") else "")
    split = "" if None in (f.get("ko_wins"), f.get("sub_wins"), f.get("dec_wins")) else f"   ({f['ko_wins']} KO · {f['sub_wins']} SUB · {f['dec_wins']} DEC)"
    sub = f"{DIV.get(f['division'], f['division'][:3].upper())}   |   {rec}{split}"
    dr.text((M, 908), sub, font=fit(dr, sub, 600, 38, px0 - 24 - M), fill=SOFT)
    # fight row
    boxes = []
    nb = f.get("next_bout")
    if nb: boxes.append(("NEXT", nb["opponent"], str(nb["event"]).split(":")[0], dmy_short(nb["date"])))
    for fight in (f.get("last_fights") or []):
        if len(boxes) == 5: break
        r = fight.get("result", "")
        kind = "W" if r == "W" else "L" if r == "L" else "D" if r.upper().startswith("D") else "NC"
        meth = fight.get("method") or ""
        if kind == "NC": meth = meth.title() if meth else "No contest"
        elif kind == "D": meth = meth or "Draw"
        boxes.append((kind, fight["opponent"], meth, dmy_short(fight["date"])))
    past = len(boxes) - (1 if nb else 0)
    head = (f"NEXT FIGHT + LAST {past}" if past else "NEXT FIGHT") if nb else (f"LAST {past} FIGHTS" if past != 1 else "LAST FIGHT")
    if boxes: dr.text((M, 1000), head, font=bc(700, 26), fill=MUTED)
    gap = 14; bw = (W - 2 * M - 4 * gap) / 5; by, bh = 1040, 214
    for i, b in enumerate(boxes): fight_box(dr, M + i * (bw + gap), by, bw, bh, *b)
    # footer
    dr.text((M, H - 66), "cagecoins.com", font=bc(700, 34), fill=GREEN)
    d1 = "(NO FIGHTER AFFILIATION)"; d2 = "Fantasy money only · Not affiliated with the UFC"
    dr.text((W - M - dr.textlength(d1, font=bc(700, 24)), H - 74), d1, font=bc(700, 24), fill=SOFT)
    dr.text((W - M - dr.textlength(d2, font=bc(600, 22)), H - 44), d2, font=bc(600, 22), fill=MUTED)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.save(out, "PNG", optimize=True)
