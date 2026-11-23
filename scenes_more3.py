"""Scenes: MYTH/FACT stamps, big numbers, car in snow, thermometer, airplane, cell tower, hot phone."""
import math, random
import make_video as mv
from tech_scenes import _car, _skyline, lm_phone
from scenes_more import _txt

def lm_stamp(img, d, cx, by, sc, ctx, word="MYTH", col=(230, 60, 60)):
    from PIL import Image, ImageDraw
    w, h = 760, 300
    s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(s)
    sd.rounded_rectangle([10, 10, w - 10, h - 10], 40, outline=col + (255,), width=22)
    sd.text((w / 2, h / 2), word, font=mv.font(190), fill=col + (255,), anchor="mm")
    s = s.rotate(-9, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(s, (int(cx - s.width / 2), int(by - 760 - s.height / 2)))

def lm_bignum(img, d, cx, by, sc, ctx, n="1", sub=""):
    d.ellipse([cx - 260, by - 1000, cx + 260, by - 480], fill=(255, 206, 84))
    _txt(d, cx, by - 750, "#" + n, 260, (30, 36, 54))
    if sub:
        _txt(d, cx, by - 380, sub, 76, (255, 255, 255))

def lm_snowcar(img, d, cx, by, sc, ctx, smoke=True):
    _skyline(d, cx, by - 20, sc, seed=51, hmax=360)
    _car(d, cx + 60, by + 20, sc, col=(226, 76, 70), s=0.9)
    snow = (248, 250, 255)
    d.ellipse([cx - 230, by - 220, cx + 330, by - 150], fill=snow)          # snow on roof
    for x in range(int(cx - 700), int(cx + 700), 90):
        d.ellipse([x, by - 10, x + 140, by + 70], fill=snow)
    if smoke:
        ex = cx + 60 + 560 * 0.9 / 2
        for i in range(5):
            r = 26 + i * 16
            d.ellipse([ex + 20 + i * 50 - r, by - 60 - i * 40 - r, ex + 20 + i * 50 + r, by - 60 - i * 40 + r], fill=(206, 212, 224))

def lm_thermo(img, d, cx, by, sc, ctx, level=0.2, label=""):
    x0, top, bot = cx - 60, by - 1000, by - 260
    d.rounded_rectangle([x0, top, x0 + 120, bot], 60, fill=(236, 240, 248))
    d.ellipse([cx - 120, bot - 60, cx + 120, bot + 180], fill=(236, 240, 248))
    col = (80, 170, 255) if level < 0.5 else (255, 96, 84)
    d.ellipse([cx - 90, bot - 30, cx + 90, bot + 150], fill=col)
    y = bot - (bot - top - 60) * level
    d.rounded_rectangle([x0 + 30, y, x0 + 90, bot + 20], 30, fill=col)
    for k in range(7):
        yy = top + 60 + k * (bot - top - 80) / 6
        d.rectangle([x0 + 130, yy, x0 + 170, yy + 8], fill=(236, 240, 248))
    if label:
        _txt(d, cx + 300, (top + bot) / 2, label, 110, col)

def _plane(d, x, y, s=1.0, col=(240, 244, 250)):
    d.rounded_rectangle([x - 260 * s, y - 40 * s, x + 260 * s, y + 40 * s], int(40 * s), fill=col)
    d.polygon([(x - 40 * s, y), (x + 60 * s, y), (x - 120 * s, y + 200 * s), (x - 180 * s, y + 200 * s)], fill=mv.dk(col, 0.85))
    d.polygon([(x - 40 * s, y - 10 * s), (x + 60 * s, y - 10 * s), (x - 60 * s, y - 150 * s), (x - 110 * s, y - 150 * s)], fill=mv.dk(col, 0.8))
    d.polygon([(x - 260 * s, y - 30 * s), (x - 200 * s, y - 30 * s), (x - 250 * s, y - 140 * s), (x - 290 * s, y - 140 * s)], fill=mv.dk(col, 0.8))
    for k in range(6):
        wx = x - 120 * s + k * 50 * s
        d.ellipse([wx, y - 18 * s, wx + 22 * s, y + 4 * s], fill=(80, 140, 200))
    d.ellipse([x + 200 * s, y - 26 * s, x + 262 * s, y + 10 * s], fill=(80, 140, 200))

def lm_plane_high(img, d, cx, by, sc, ctx):
    for i in range(6):                                 # cloud layer below
        x = cx - 640 + i * 240
        d.ellipse([x, by - 380, x + 320, by - 200], fill=(250, 252, 255))
    _plane(d, cx, by - 780, 1.0)
    _txt(d, cx, by - 1080, "35,000 ft", 110, (255, 255, 255))

def lm_plane_low(img, d, cx, by, sc, ctx):
    _skyline(d, cx, by, sc, seed=61, hmax=320)
    _plane(d, cx, by - 640, 0.8)
    for k in range(3):
        y = by - 520 + k * 60
        d.line([(cx + 240, y), (cx + 520, y)], fill=(150, 170, 200), width=10)

def lm_tower(img, d, cx, by, sc, ctx, bars=1):
    t = (120, 130, 150)
    d.polygon([(cx - 140, by), (cx + 140, by), (cx + 20, by - 800), (cx - 20, by - 800)], outline=t, width=14)
    for k in range(6):
        y = by - 120 - k * 120
        w = 140 - k * 20
        d.line([(cx - w, y), (cx + w, y)], fill=t, width=10)
    for i, r in enumerate((90, 160, 230)):
        d.arc([cx - r, by - 830 - r, cx + r, by - 830 + r], 300, 60, fill=(80, 200, 255), width=12)
    x0 = cx + 260
    for i in range(4):
        h = 60 + i * 50
        d.rounded_rectangle([x0 + i * 60, by - 400 - h, x0 + i * 60 + 40, by - 400], 8,
                            fill=(92, 230, 150) if i < bars else (70, 78, 104))

def lm_phone_hot(img, d, cx, by, sc, ctx):
    lm_phone(img, d, cx, by, sc, ctx)
    heat = (255, 110, 80)
    for k in range(4):
        x = cx - 180 + k * 120
        pts = [(x + 24 * math.sin(i / 3), by - 820 - i * 18) for i in range(10)]
        d.line(pts, fill=heat, width=14, joint="curve")

def lm_brightness(img, d, cx, by, sc, ctx):
    lm_phone(img, d, cx, by, sc, ctx)
    sx, sy = cx, by - 1000
    d.ellipse([sx - 70, sy - 70, sx + 70, sy + 70], fill=(255, 220, 80))
    for k in range(12):
        a = k / 12 * 6.283
        d.line([(sx + 95 * math.cos(a), sy + 95 * math.sin(a)), (sx + 140 * math.cos(a), sy + 140 * math.sin(a))], fill=(255, 220, 80), width=14)

def lm_gps(img, d, cx, by, sc, ctx):
    lm_phone(img, d, cx, by, sc, ctx)
    px, py = cx, by - 1010
    d.ellipse([px - 80, py - 80, px + 80, py + 80], fill=(230, 60, 60))
    d.polygon([(px - 70, py + 30), (px + 70, py + 30), (px, py + 160)], fill=(230, 60, 60))
    d.ellipse([px - 32, py - 32, px + 32, py + 32], fill=(255, 255, 255))

mv.LANDMARKS.update({
    "myth": lm_stamp, "fact": lambda *a: lm_stamp(*a, word="FACT", col=(40, 190, 110)),
    "num1": lambda *a: lm_bignum(*a, n="1"), "num2": lambda *a: lm_bignum(*a, n="2"), "num3": lambda *a: lm_bignum(*a, n="3"),
    "snowcar": lm_snowcar, "snowcar_off": lambda *a: lm_snowcar(*a, smoke=False),
    "thermo_cold": lambda *a: lm_thermo(*a, level=0.15), "thermo_warm": lambda *a: lm_thermo(*a, level=0.75),
    "plane_high": lm_plane_high, "plane_low": lm_plane_low,
    "tower_weak": lambda *a: lm_tower(*a, bars=1), "tower_full": lambda *a: lm_tower(*a, bars=4),
    "phone_hot": lm_phone_hot, "brightness": lm_brightness, "gps": lm_gps,
})

def lm_yesno(img, d, cx, by, sc, ctx, a="YES", b="NO"):
    d.text((cx, by - 1010), "COMMENT", font=mv.font(120), fill=(255, 214, 64), anchor="mm", stroke_width=10, stroke_fill=(30, 36, 54))
    for x0, word, col in ((cx - 420, a, (40, 190, 110)), (cx + 20, b, (230, 60, 60))):
        d.rounded_rectangle([x0 + 8, by - 892, x0 + 408, by - 692], 90, fill=mv.dk(col, 0.6))
        d.rounded_rectangle([x0, by - 900, x0 + 400, by - 700], 90, fill=col)
        _txt(d, x0 + 200, by - 800, word, 120, (255, 255, 255))

mv.LANDMARKS.update({"yesno": lm_yesno})
