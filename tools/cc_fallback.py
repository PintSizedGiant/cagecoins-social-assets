"""No-photo fallback for T7 to T10 (agreed 13/11/2026).
Makes a transparent PNG the same shape as a fighter cut-out: the fighter's flag as a soft panel with the
ticker stacked large over it. It drops into the existing photo slot, so the templates keep their layout.
Contains no likeness, so posts using it are not AI-labelled for that fighter."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from cc_fighter import bc, flag

def stand_in(ticker, country_code, out_dir="/tmp/cc_standin", w=700, h=900):
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{ticker}.png")
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    top, bot = int(h * 0.33), int(h * 0.63)          # keep clear of the result word above and the name below
    fl = flag(country_code, 420)
    if fl:
        s = min(w * 0.86 / fl.width, (bot - top) / fl.height)
        fl = fl.resize((int(fl.width * s), int(fl.height * s)), Image.LANCZOS)
        a = Image.new("L", fl.size, 0); ImageDraw.Draw(a).rounded_rectangle([0, 0, fl.width - 1, fl.height - 1], 36, fill=70)
        fl.putalpha(ImageChops.multiply(fl.getchannel("A"), a))
        im.alpha_composite(fl, ((w - fl.width) // 2, top + (bot - top - fl.height) // 2))
    dr = ImageDraw.Draw(im)
    t = ticker.upper(); size = 260
    while size > 80 and dr.textlength(t, font=bc(800, size)) > w * 0.80: size -= 6
    f = bc(800, size); tw = dr.textlength(t, font=f); bb = dr.textbbox((0, 0), t, font=f)
    y = top + (bot - top - (bb[3] - bb[1])) // 2 - bb[1]
    dr.text(((w - tw) / 2, y), t, font=f, fill=(240, 244, 242, 235), stroke_width=3, stroke_fill=(8, 20, 16, 255))
    # soft shadow behind so it reads on any background
    sh = im.getchannel("A").filter(ImageFilter.GaussianBlur(18)).point(lambda v: v // 3)
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0)); base.putalpha(sh)
    base.alpha_composite(im)
    base.putpixel((0, 0), (0, 0, 0, 1)); base.putpixel((w - 1, h - 1), (0, 0, 0, 1))  # keep the full frame when the templates crop to content
    base.save(out)
    return out
