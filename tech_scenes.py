"""Tech / modern scenes for Bolt Knows Why. Importing this module registers a "city" terrain
and new landmarks (skyline, evcharger, phone, battery20/80/100, parking_empty/full) in make_video."""
import math
import make_video as mv

mv.TERRAIN["city"] = dict(far=(120, 134, 168), mid=(86, 92, 110), near=(58, 62, 78))

# ---------------------------------------------------------------- tech landmarks
def _skyline(d, cx, by, sc, n=9, seed=5, hmax=620):
    import random as _r
    r = _r.Random(seed)
    x = cx - 620
    for i in range(n):
        w = r.randint(90, 170); h = r.randint(220, hmax)
        base = sc((92 + r.randint(-14, 14), 108 + r.randint(-14, 14), 150 + r.randint(-10, 20)))
        d.rectangle([x, by - h, x + w, by], fill=base)
        d.rectangle([x + w * 0.72, by - h, x + w, by], fill=mv.dk(base, 0.82))
        for yy in range(int(by - h + 24), int(by - 30), 46):
            for xx in range(int(x + 16), int(x + w - 26), 34):
                on = r.random() < 0.55
                d.rectangle([xx, yy, xx + 16, yy + 24], fill=sc((255, 226, 140)) if on else mv.dk(base, 0.7))
        x += w + r.randint(6, 26)

def lm_skyline(img, d, cx, by, sc, ctx):
    _skyline(d, cx, by, sc)

def _car(d, x, by, sc, col=(40, 190, 170), s=1.0):
    body, dark, glass = sc(col), mv.dk(sc(col), 0.7), sc((190, 228, 246))
    L, Hh = 560 * s, 120 * s
    d.rounded_rectangle([x - L / 2, by - 70 * s - Hh, x + L / 2, by - 70 * s], int(46 * s), fill=body)
    d.polygon([(x - L * 0.30, by - 70 * s - Hh + 6), (x - L * 0.18, by - 70 * s - Hh - 96 * s), (x + L * 0.20, by - 70 * s - Hh - 96 * s),
               (x + L * 0.36, by - 70 * s - Hh + 6)], fill=body)
    d.polygon([(x - L * 0.25, by - 70 * s - Hh), (x - L * 0.155, by - 70 * s - Hh - 78 * s), (x - L * 0.01, by - 70 * s - Hh - 78 * s),
               (x - L * 0.01, by - 70 * s - Hh)], fill=glass)
    d.polygon([(x + L * 0.02, by - 70 * s - Hh), (x + L * 0.02, by - 70 * s - Hh - 78 * s), (x + L * 0.185, by - 70 * s - Hh - 78 * s),
               (x + L * 0.30, by - 70 * s - Hh)], fill=glass)
    d.rectangle([x - L / 2 + 20 * s, by - 86 * s, x + L / 2 - 20 * s, by - 70 * s], fill=dark)
    d.rounded_rectangle([x + L / 2 - 38 * s, by - 150 * s, x + L / 2 - 6 * s, by - 126 * s], 8, fill=sc((255, 244, 190)))
    for wx in (x - L * 0.30, x + L * 0.30):
        d.ellipse([wx - 62 * s, by - 124 * s, wx + 62 * s, by], fill=(28, 30, 38))
        d.ellipse([wx - 30 * s, by - 92 * s, wx + 30 * s, by - 32 * s], fill=sc((200, 206, 216)))
    return x - L / 2 + 30 * s, by - 150 * s      # charge port position

def lm_evcharger(img, d, cx, by, sc, ctx):
    _skyline(d, cx, by - 10, sc, seed=11, hmax=420)
    px, py = _car(d, cx + 150, by + 20, sc, s=0.9)
    # charging post
    post, dark = sc((236, 240, 246)), sc((60, 70, 92))
    x0 = cx - 330
    d.rounded_rectangle([x0 - 80, by - 430, x0 + 80, by + 20], 26, fill=post)
    d.rounded_rectangle([x0 - 56, by - 396, x0 + 56, by - 250], 14, fill=dark)
    d.polygon([(x0 + 10, by - 380), (x0 - 26, by - 318), (x0 - 2, by - 318), (x0 - 14, by - 266), (x0 + 28, by - 334), (x0 + 4, by - 334)],
              fill=sc((120, 255, 190)))
    d.rounded_rectangle([x0 - 56, by - 226, x0 + 56, by - 200], 8, fill=sc((40, 200, 150)))
    # cable
    pts = []
    for i in range(41):
        t = i / 40
        xx = x0 + 80 + (px - x0 - 80) * t
        yy = (by - 300) * (1 - t) + py * t + math.sin(t * math.pi) * 170
        pts.append((xx, yy))
    d.line(pts, fill=(30, 34, 44), width=16, joint="curve")
    d.ellipse([px - 18, py - 18, px + 18, py + 18], fill=sc((120, 255, 190)))

def lm_battery(img, d, cx, by, sc, ctx, level=0.8):
    w, h = 420, 700
    x0, y0 = cx - w / 2, by - h - 60
    shell = sc((232, 238, 246))
    d.rounded_rectangle([cx - 80, y0 - 50, cx + 80, y0 + 10], 18, fill=shell)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 56, fill=shell)
    d.rounded_rectangle([x0 + 28, y0 + 28, x0 + w - 28, y0 + h - 28], 36, fill=sc((36, 44, 66)))
    segs = 10
    full = int(round(level * segs))
    sh = (h - 56 - 24 - (segs - 1) * 12) / segs
    for i in range(segs):
        yb = y0 + h - 28 - 12 - i * (sh + 12)
        if i < full:
            col = (255, 96, 84) if level <= 0.2 else ((255, 206, 84) if i >= 8 else (92, 230, 150))
            d.rounded_rectangle([x0 + 46, yb - sh, x0 + w - 46, yb], 12, fill=sc(col))
        else:
            d.rounded_rectangle([x0 + 46, yb - sh, x0 + w - 46, yb], 12, outline=sc((90, 104, 136)), width=4)
    f = mv.font(120)
    txt = f"{int(level * 100)}%"
    tw = d.textlength(txt, font=f)
    d.text((cx - tw / 2 + 4, y0 - 210 + 4), txt, font=f, fill=(0, 0, 0, 120))
    d.text((cx - tw / 2, y0 - 210), txt, font=f, fill=(255, 255, 255))

def lm_parking(img, d, cx, by, sc, ctx, filled=0.5):
    """Top-down parking lot = lithium ions finding free spots in the battery."""
    import random as _r
    r = _r.Random(3)
    cols, rows, cw, ch = 5, 5, 138, 116
    x0, y0 = cx - cols * cw / 2, by - rows * ch - 90
    d.rounded_rectangle([x0 - 30, y0 - 30, x0 + cols * cw + 30, y0 + rows * ch + 30], 30, fill=sc((52, 58, 76)))
    cells = [(i, j) for j in range(rows) for i in range(cols)]
    r.shuffle(cells)
    taken = set(cells[:int(len(cells) * filled)])
    for (i, j) in cells:
        x, y = x0 + i * cw, y0 + j * ch
        d.rectangle([x + 6, y + 6, x + cw - 6, y + ch - 6], outline=sc((230, 232, 240)), width=4)
        if (i, j) in taken:
            col = r.choice([(92, 230, 150), (80, 200, 255), (255, 206, 84), (255, 128, 110)])
            d.rounded_rectangle([x + 26, y + 24, x + cw - 26, y + ch - 24], 22, fill=sc(col))
            d.rounded_rectangle([x + 44, y + 36, x + cw - 44, y + ch - 36], 12, fill=mv.dk(sc(col), 0.75))

def lm_phone(img, d, cx, by, sc, ctx):
    w, h = 380, 720
    x0, y0 = cx - w / 2, by - h - 40
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 60, fill=sc((30, 34, 46)))
    d.rounded_rectangle([x0 + 18, y0 + 18, x0 + w - 18, y0 + h - 18], 46, fill=sc((24, 60, 96)))
    d.rounded_rectangle([cx - 60, y0 + 34, cx + 60, y0 + 58], 12, fill=sc((14, 18, 26)))
    d.polygon([(cx + 30, y0 + 210), (cx - 70, y0 + 390), (cx - 6, y0 + 390), (cx - 36, y0 + 540), (cx + 76, y0 + 340), (cx + 10, y0 + 340)],
              fill=sc((120, 255, 190)))
    d.line([(cx, y0 + h), (cx, by + 40)], fill=(236, 240, 246), width=14)


mv.LANDMARKS.update({
    "skyline": lm_skyline, "evcharger": lm_evcharger, "phone": lm_phone,
    "battery20": lambda *a: lm_battery(*a, level=0.2), "battery80": lambda *a: lm_battery(*a, level=0.8),
    "battery100": lambda *a: lm_battery(*a, level=1.0),
    "parking_empty": lambda *a: lm_parking(*a, filled=0.2), "parking_full": lambda *a: lm_parking(*a, filled=0.87),
})
