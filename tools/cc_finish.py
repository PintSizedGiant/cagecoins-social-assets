"""Cage Coins FINISH card, template T8 (13/11/2026).
For a fighter who won or lost by KO/TKO or submission at the last card.
Big result word behind the fighter, result chip in front, price before and now, and a 'how it ended' row.
Shares background, fonts, flags and fighter placement with T7 (cc_fighter.py). 1080x1350 PNG, no metadata."""
import os
from PIL import Image, ImageDraw
import cc_fighter as F
from cc_fighter import W, H, M, WHITE, SOFT, MUTED, GREEN, RED, GREY, bc, fit, money, flag, place_fighter, DIV

def finish_kind(method):
    m = (method or "").upper()
    if m.startswith("KO") or "TKO" in m: return "KO"
    if m.startswith("SUB"): return "SUB"
    return None

def card(f, photo_path, out):
    """f: name ticker country_code division wins losses draws ko_wins sub_wins dec_wins
          won (bool) method opponent event event_date old new [round] [time]"""
    kind = finish_kind(f["method"])
    if not kind: raise ValueError("T8 is only for KO/TKO or submission results")
    won = bool(f["won"]); col = GREEN if won else RED
    seed = sum(ord(c) for c in f["ticker"]) + 7
    im = F.background(seed, (74, 222, 128) if won else (248, 113, 113))
    if not won: im = im.transpose(Image.FLIP_LEFT_RIGHT)        # falling chart for a loss
    # big result word, drawn behind the fighter
    word = "KNOCKOUT" if kind == "KO" else "SUBMISSION"
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    wf = fit(ld, word, 800, 330, W - 2 * M)
    ww = ld.textlength(word, font=wf)
    ld.text(((W - ww) / 2, 92), word, font=wf, fill=col + (46,), stroke_width=4, stroke_fill=col + (210,))
    im.paste(layer, (0, 0), layer)
    if photo_path and os.path.exists(photo_path): place_fighter(im, photo_path)
    dr = ImageDraw.Draw(im)
    # header
    dr.text((M, 40), "CAGECOINS", font=bc(800, 58), fill=WHITE)
    lab = f"{str(f['event']).split(':')[0].upper()} · {F.dmy_short(f['event_date'])}"
    lf = fit(dr, lab, 600, 28, 520); dr.text((W - M - dr.textlength(lab, font=lf), 54), lab, font=lf, fill=SOFT)
    # result chip, in front of the fighter
    chip = f"{'WIN' if won else 'LOSS'} BY {'KO/TKO' if kind == 'KO' else 'SUBMISSION'}"
    cf = bc(800, 54); cw = dr.textlength(chip, font=cf)
    dr.rounded_rectangle([M, 640, M + cw + 48, 716], 14, fill=col)
    dr.text((M + 24, 648), chip, font=cf, fill=(8, 14, 12))
    # price panel
    up = f["new"] >= f["old"]; pcol = GREEN if up else RED
    chg = f["new"] - f["old"]; pct = chg / f["old"] * 100 if f["old"] else 0
    px0, py0, px1, py1 = 690, 748, W - M, 972
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([px0, py0, px1, py1], 22, fill=(pcol[0] // 6, pcol[1] // 6, pcol[2] // 6, 225), outline=pcol + (255,), width=3)
    im.paste(panel, (0, 0), panel); dr = ImageDraw.Draw(im)
    bt = f"BEFORE  {money(f['old'])}"
    dr.text((px0 + 28, py0 + 22), bt, font=fit(dr, bt, 600, 28, px1 - px0 - 56), fill=SOFT)
    nt = money(f["new"]); dr.text((px0 + 26, py0 + 52), nt, font=fit(dr, nt, 800, 96, px1 - px0 - 52), fill=WHITE)
    ty = py0 + 166
    tri = [(px0 + 28, ty + 26), (px0 + 52, ty + 26), (px0 + 40, ty + 6)] if up else [(px0 + 28, ty + 6), (px0 + 52, ty + 6), (px0 + 40, ty + 26)]
    dr.polygon(tri, fill=pcol)
    ct = f"{'+' if up else '-'}{abs(pct):.2f}%    {'+' if up else '-'}{money(abs(chg))}"
    dr.text((px0 + 64, ty - 4), ct, font=fit(dr, ct, 700, 36, px1 - px0 - 92), fill=pcol)
    # name block
    fl = flag(f.get("country_code"), 58); nx = M
    if fl:
        im.paste(fl, (M, 818), fl); nx = M + fl.width + 20
    name = f["name"].upper(); nf = fit(dr, name, 800, 118, px0 - 24 - nx)
    dr.text((nx, 846 - nf.size * 0.62), name, font=nf, fill=WHITE)
    rec = f"{f['wins']}-{f['losses']}" + (f"-{f['draws']}" if f.get("draws") else "")
    split = "" if None in (f.get("ko_wins"), f.get("sub_wins"), f.get("dec_wins")) else f"   ({f['ko_wins']} KO · {f['sub_wins']} SUB · {f['dec_wins']} DEC)"
    sub = f"{DIV.get(f['division'], f['division'][:3].upper())}   |   {rec}{split}"
    dr.text((M, 908), sub, font=fit(dr, sub, 600, 38, px0 - 24 - M), fill=SOFT)
    # how it ended
    boxes = [("OPPONENT", f["opponent"], None), ("METHOD", "KO/TKO" if kind == "KO" else (f["method"] or "Submission"), None)]
    if f.get("round"): boxes.append(("ROUND", f"R{f['round']}", f.get("time")))
    boxes.append(("EVENT", str(f["event"]).split(":")[0], F.dmy_short(f["event_date"])))
    dr.text((M, 1000), "HOW IT ENDED", font=bc(700, 26), fill=MUTED)
    gap = 14; n = len(boxes); bw = (W - 2 * M - (n - 1) * gap) / n; by, bh = 1040, 214
    for i, (head, main, extra) in enumerate(boxes):
        x = M + i * (bw + gap)
        dr.rounded_rectangle([x, by, x + bw, by + bh], 16, fill=(col[0] // 7, col[1] // 7, col[2] // 7), outline=col, width=3)
        dr.rectangle([x + 3, by + 3, x + bw - 3, by + 8], fill=col)
        dr.text((x + 18, by + 22), head, font=bc(800, 28), fill=col)
        if head == "OPPONENT":
            parts = main.split(" ", 1); first, last = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])
            if first: dr.text((x + 18, by + 70), first, font=fit(dr, first, 600, 30, bw - 36), fill=SOFT)
            dr.text((x + 18, by + 104), last.upper(), font=fit(dr, last.upper(), 800, 52, bw - 36), fill=WHITE)
        else:
            dr.text((x + 18, by + 80), main.upper(), font=fit(dr, main.upper(), 800, 60, bw - 36), fill=WHITE)
            if extra: dr.text((x + 18, by + 156), extra, font=fit(dr, extra, 600, 30, bw - 36), fill=SOFT)
    # footer
    dr.text((M, H - 66), "cagecoins.com", font=bc(700, 34), fill=GREEN)
    d1 = "(NO FIGHTER AFFILIATION)"; d2 = "Fantasy money only · Not affiliated with the UFC"
    dr.text((W - M - dr.textlength(d1, font=bc(700, 24)), H - 74), d1, font=bc(700, 24), fill=SOFT)
    dr.text((W - M - dr.textlength(d2, font=bc(600, 22)), H - 44), d2, font=bc(600, 22), fill=MUTED)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.save(out, "PNG", optimize=True)
