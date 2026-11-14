#!/usr/bin/env python3
"""
YouTube Shorts renderer — everything is drawn with code (no paid video API).
  * storybook-style animated scenes (parallax layers, camera zoom, particles)
  * child narrator voice (free Microsoft Edge TTS, voice "en-US-AnaNeural")
  * word-by-word karaoke subtitles + hook title card + end card
  * soft generated background music (no copyright issues)

Usage:
  python make_video.py --topic 0 --out out/video.mp4          # full video with voice
  python make_video.py --topic 0 --out sample.mp4 --no-tts    # silent preview (no internet)
"""
import argparse, asyncio, json, math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
HORIZON = int(H * 0.60)
VOICE = os.environ.get("TTS_VOICE", "en-US-AnaNeural")
RATE = os.environ.get("TTS_RATE", "-6%")
PITCH = os.environ.get("TTS_PITCH", "+0Hz")
VOICE_DELAY = 0.30   # seconds of silence before narration
TAIL = 1.4           # seconds after narration (end card)
XF = 0.45            # scene crossfade

# ---------------------------------------------------------------- helpers
def font(size):
    for p in [os.path.join(HERE, "assets", "Poppins-Bold.ttf"),
              "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def dk(c, f=0.72):
    return tuple(int(v * f) for v in c[:3])

PAL = {
    "day":    dict(top=(70, 140, 222), bot=(192, 224, 246), sun=(255, 246, 205), tint=None, amt=0.0),
    "dawn":   dict(top=(92, 118, 196), bot=(255, 198, 162), sun=(255, 228, 172), tint=(255, 168, 140), amt=0.22),
    "sunset": dict(top=(56, 36, 102), bot=(255, 138, 82), sun=(255, 206, 128), tint=(112, 50, 92), amt=0.42),
    "night":  dict(top=(8, 12, 36), bot=(36, 46, 100), sun=(236, 238, 255), tint=(18, 24, 62), amt=0.70),
}

TERRAIN = {
    "desert":    dict(far=(232, 196, 138), mid=(218, 168, 102), near=(192, 134, 74)),
    "grass":     dict(far=(132, 176, 118), mid=(92, 152, 82), near=(62, 120, 60)),
    "mountains": dict(far=(132, 142, 172), mid=(98, 124, 110), near=(64, 94, 72)),
    "jungle":    dict(far=(74, 132, 94), mid=(44, 108, 64), near=(26, 78, 44)),
    "sea":       dict(far=(108, 128, 150), mid=(40, 112, 164), near=(24, 82, 132)),
    "snow":      dict(far=(206, 216, 234), mid=(232, 238, 248), near=(248, 250, 255)),
    "canyon":    dict(far=(214, 128, 86), mid=(186, 92, 58), near=(150, 70, 44)),
}

def shade(c, pal, depth=0.0):
    if pal["tint"]:
        c = mix(c, pal["tint"], pal["amt"])
    return mix(c, pal["bot"], depth * 0.55)

def ridge(width, base, amp, seed, jag=False, step=6):
    rnd = random.Random(seed)
    comps = [(rnd.uniform(0.0022, 0.0060) * (1.7 if jag else 1.0), rnd.uniform(0, 6.28), rnd.uniform(0.45, 1.0))
             for _ in range(4)]
    tot = sum(c[2] for c in comps)
    xs = list(range(0, width + step, step))
    ys = []
    for x in xs:
        v = 0.0
        for f, ph, a in comps:
            s = math.sin(x * f + ph)
            v += a * ((1 - abs(s)) * 2 - 1 if jag else s)
        ys.append(base - amp * v / tot)
    return xs, ys

def ridge_fn(xs, ys):
    step = xs[1] - xs[0]
    def f(x):
        i = int(max(0, min(len(xs) - 2, x // step)))
        t = (x - xs[i]) / step
        return ys[i] + (ys[i + 1] - ys[i]) * t
    return f

def poly_layer(width, xs, ys, color):
    im = Image.new("RGBA", (width, H), (0, 0, 0, 0))
    pts = list(zip(xs, ys)) + [(width, H), (0, H)]
    ImageDraw.Draw(im).polygon(pts, fill=tuple(color) + (255,))
    return im

def crop_layer(im):
    bb = im.getbbox()
    if not bb:
        return im, 0
    return im.crop((0, bb[1], im.width, im.height)), bb[1]

# ---------------------------------------------------------------- landmarks
# signature: fn(img, d, cx, by, sc, ctx) — sc(color) shades a colour for the scene's light
def lm_pyramids(img, d, cx, by, sc, ctx):
    lit, dark, line = sc((236, 198, 134)), sc((176, 132, 80)), sc((206, 166, 104))
    for dx, h, w in [(-340, 300, 430), (380, 250, 350), (30, 560, 760)]:
        ax, ay = cx + dx, by - h
        l, r, m = cx + dx - w / 2, cx + dx + w / 2, cx + dx + w * 0.14
        d.polygon([(l, by), (ax, ay), (m, by)], fill=lit)
        d.polygon([(m, by), (ax, ay), (r, by)], fill=dark)
        for yy in range(int(ay) + 28, int(by), 26):
            k = (yy - ay) / h
            d.line([(ax - w / 2 * k, yy), (ax + (m - ax) * k, yy)], fill=line, width=2)

def lm_sphinx(img, d, cx, by, sc, ctx):
    lit, dark = sc((226, 186, 124)), sc((170, 126, 78))
    # small pyramid behind
    d.polygon([(cx - 520, by), (cx - 250, by - 330), (cx + 40, by)], fill=sc((214, 178, 122)))
    d.polygon([(cx - 210, by), (cx - 250, by - 330), (cx + 40, by)], fill=sc((180, 140, 92)))
    d.rounded_rectangle([cx - 360, by - 170, cx + 260, by], 60, fill=lit)          # body
    d.rounded_rectangle([cx - 360, by - 90, cx + 180, by], 30, fill=dark)          # flank shadow
    d.rounded_rectangle([cx + 200, by - 50, cx + 440, by], 20, fill=lit)           # paws
    d.polygon([(cx + 150, by - 150), (cx + 190, by - 380), (cx + 330, by - 380), (cx + 360, by - 150)], fill=dark)  # headdress
    d.rounded_rectangle([cx + 205, by - 360, cx + 315, by - 175], 30, fill=lit)    # face
    d.rectangle([cx + 250, by - 300, cx + 300, by - 290], fill=dark)               # eye
    d.rectangle([cx + 245, by - 220, cx + 290, by - 212], fill=dark)               # mouth

def lm_stonehenge(img, d, cx, by, sc, ctx):
    for row, (yo, scl, depth) in enumerate([(-40, 0.7, 0.35), (0, 1.0, 0.0)]):
        col = sc(mix((150, 150, 146), (200, 205, 215), depth))
        drk = sc(mix((104, 104, 102), (170, 175, 190), depth))
        n = 6 if row == 0 else 4
        span = 900 * scl
        for i in range(n):
            x = cx - span / 2 + span * i / (n - 1)
            w, h = 52 * scl, 240 * scl
            y0 = by + yo
            for dx in (-w * 0.9, w * 0.9):
                d.rectangle([x + dx - w / 2, y0 - h, x + dx + w / 2, y0], fill=col)
                d.rectangle([x + dx + w * 0.15, y0 - h, x + dx + w / 2, y0], fill=drk)
            if i % 2 == 0 or row == 1:
                d.rectangle([x - w * 1.6, y0 - h - 34 * scl, x + w * 1.6, y0 - h + 4], fill=col)
    d.polygon([(cx + 470, by + 30), (cx + 490, by - 160), (cx + 560, by - 150), (cx + 570, by + 30)], fill=sc((120, 118, 112)))

def lm_temple(img, d, cx, by, sc, ctx):
    lit, dark, line = sc((238, 232, 216)), sc((188, 180, 162)), sc((205, 198, 182))
    w = 820
    for i in range(3):
        d.rectangle([cx - w / 2 - 40 + i * 14, by - 24 * (i + 1), cx + w / 2 + 40 - i * 14, by - 24 * i], fill=lit if i % 2 == 0 else dark)
    top = by - 72
    n, cw, ch = 8, 58, 330
    for i in range(n):
        x = cx - w / 2 + 40 + (w - 80) * i / (n - 1)
        d.rectangle([x - cw / 2, top - ch, x + cw / 2, top], fill=lit)
        d.rectangle([x + cw * 0.15, top - ch, x + cw / 2, top], fill=dark)
        for f in (-14, 0):
            d.line([(x + f, top - ch + 8), (x + f, top - 8)], fill=line, width=2)
    d.rectangle([cx - w / 2 - 10, top - ch - 70, cx + w / 2 + 10, top - ch], fill=lit)
    d.rectangle([cx - w / 2 - 10, top - ch - 34, cx + w / 2 + 10, top - ch - 28], fill=dark)
    d.polygon([(cx - w / 2 - 20, top - ch - 70), (cx, top - ch - 210), (cx + w / 2 + 20, top - ch - 70)], fill=dark)
    d.polygon([(cx - w / 2 + 30, top - ch - 80), (cx, top - ch - 190), (cx + w / 2 - 30, top - ch - 80)], fill=lit)

def lm_colosseum(img, d, cx, by, sc, ctx):
    lit, dark, hole = sc((224, 192, 150)), sc((172, 140, 104)), sc((96, 70, 52))
    w, th = 900, 92
    for tier in range(4):
        y1 = by - tier * th
        frac = 1.0 if tier < 3 else 0.62
        x0, x1 = cx - w / 2, cx - w / 2 + w * frac
        if tier == 3:
            d.polygon([(x0, y1), (x0, y1 - th), (x1, y1 - th), (x1 + 60, y1)], fill=lit)
        else:
            d.rectangle([x0, y1 - th, x1, y1], fill=lit)
        d.rectangle([x0, y1 - 10, x1, y1], fill=dark)
        if tier < 3:
            n = 11
            for i in range(n):
                ax = x0 + 30 + (w - 60) * (i + 0.5) / n
                d.rounded_rectangle([ax - 22, y1 - th + 18, ax + 22, y1 - 12], 22, fill=hole)
    # ruined right side
    d.polygon([(cx + w / 2, by), (cx + w / 2, by - 3 * th), (cx + w / 2 + 80, by - 2 * th), (cx + w / 2 + 110, by)], fill=dark)

def lm_greatwall(img, d, cx, by, sc, ctx):
    g = ctx["ground"]
    lit, dark = sc((176, 156, 124)), sc((122, 106, 84))
    pts = [(x, g(x) - 6) for x in range(0, img.width, 10)]
    d.line(pts, fill=dark, width=58, joint="curve")
    d.line([(x, y - 14) for x, y in pts], fill=lit, width=34, joint="curve")
    for x in range(0, img.width, 34):
        y = g(x) - 46
        d.rectangle([x, y - 16, x + 16, y], fill=lit)
    for x in range(140, img.width, 330):
        y = g(x)
        d.rectangle([x - 44, y - 150, x + 44, y], fill=lit)
        d.rectangle([x + 10, y - 150, x + 44, y], fill=dark)
        d.rectangle([x - 14, y - 110, x + 6, y - 80], fill=sc((70, 60, 50)))
        for k in range(4):
            d.rectangle([x - 44 + k * 26, y - 170, x - 30 + k * 26, y - 150], fill=lit)

def _moai(d, x, by, s, lit, dark):
    pts = [(-60, 0), (-62, -250), (-44, -300), (40, -306), (52, -276), (78, -196), (52, -172),
           (58, -128), (46, -94), (52, 0)]
    P = [(x + px * s, by + py * s) for px, py in pts]
    d.polygon(P, fill=lit)
    d.polygon([P[0], P[1], P[2], (x - 20 * s, by - 300 * s), (x - 24 * s, by)], fill=dark)
    d.rectangle([x + 10 * s, by - 250 * s, x + 48 * s, by - 236 * s], fill=dark)

def lm_moai(img, d, cx, by, sc, ctx):
    lit, dark = sc((116, 104, 98)), sc((76, 68, 64))
    d.rectangle([cx - 480, by - 24, cx + 470, by + 10], fill=sc((96, 90, 84)))
    for x, s in [(-380, 0.85), (-160, 1.05), (80, 1.25), (330, 1.0)]:
        _moai(d, cx + x, by - 20, s, lit, dark)

def lm_mayan(img, d, cx, by, sc, ctx):
    lit, dark, stair = sc((206, 194, 166)), sc((150, 140, 116)), sc((226, 216, 190))
    tiers, th, w0 = 9, 46, 860
    for i in range(tiers):
        w = w0 - i * 64
        y1 = by - i * th
        d.rectangle([cx - w / 2, y1 - th, cx + w / 2, y1], fill=lit)
        d.rectangle([cx + w * 0.18, y1 - th, cx + w / 2, y1], fill=dark)
        d.line([(cx - w / 2, y1 - 4), (cx + w / 2, y1 - 4)], fill=dark, width=4)
    top = by - tiers * th
    d.polygon([(cx - 70, by), (cx - 46, top), (cx + 46, top), (cx + 70, by)], fill=stair)
    for y in range(int(top) + 10, int(by), 14):
        d.line([(cx - 66, y), (cx + 66, y)], fill=dark, width=2)
    d.rectangle([cx - 120, top - 120, cx + 120, top], fill=lit)
    d.rectangle([cx + 30, top - 120, cx + 120, top], fill=dark)
    d.rectangle([cx - 30, top - 80, cx + 30, top], fill=sc((70, 60, 50)))
    d.rectangle([cx - 136, top - 140, cx + 136, top - 120], fill=dark)

def lm_angkor(img, d, cx, by, sc, ctx):
    lit, dark = sc((156, 144, 122)), sc((108, 98, 84))
    d.rectangle([0, by + 6, img.width, by + 70], fill=sc((70, 120, 150)))      # moat
    for i, w in enumerate([980, 820, 640]):
        y1 = by - i * 60
        d.rectangle([cx - w / 2, y1 - 60, cx + w / 2, y1], fill=lit if i % 2 == 0 else dark)
        for k in range(12):
            x = cx - w / 2 + 20 + (w - 40) * k / 11
            d.rectangle([x - 6, y1 - 46, x + 6, y1 - 12], fill=sc((80, 72, 60)))
    base = by - 180
    for dx, h, s in [(-280, 260, 0.75), (280, 260, 0.75), (-140, 320, 0.85), (140, 320, 0.85), (0, 430, 1.0)]:
        x = cx + dx
        for k in range(8):
            ww = (120 - k * 13) * s
            y = base - k * h / 8
            d.ellipse([x - ww / 2, y - h / 8 - 6, x + ww / 2, y + 6], fill=lit if k % 2 == 0 else dark)
        d.polygon([(x - 10 * s, base - h + 10), (x, base - h - 40 * s), (x + 10 * s, base - h + 10)], fill=dark)

def lm_lighthouse(img, d, cx, by, sc, ctx):
    lit, dark = sc((242, 238, 228)), sc((190, 186, 176))
    rock = sc((92, 86, 80))
    d.ellipse([cx - 360, by - 60, cx + 360, by + 90], fill=rock)
    y = by - 30
    d.rectangle([cx - 120, y - 330, cx + 120, y], fill=lit)
    d.rectangle([cx + 40, y - 330, cx + 120, y], fill=dark)
    for k in range(5):
        d.rectangle([cx - 90, y - 300 + k * 62, cx - 60, y - 270 + k * 62], fill=sc((70, 70, 80)))
    y -= 330
    d.rectangle([cx - 160, y - 18, cx + 160, y], fill=dark)
    d.polygon([(cx - 90, y), (cx - 78, y - 200), (cx + 78, y - 200), (cx + 90, y)], fill=lit)
    d.polygon([(cx + 30, y), (cx + 26, y - 200), (cx + 78, y - 200), (cx + 90, y)], fill=dark)
    y -= 200
    d.rectangle([cx - 110, y - 14, cx + 110, y], fill=dark)
    d.rectangle([cx - 52, y - 120, cx + 52, y], fill=lit)
    d.ellipse([cx - 40, y - 190, cx + 40, y - 110], fill=(255, 190, 80))
    ctx["anchors"]["beam"] = (cx, y - 150)

def lm_volcano(img, d, cx, by, sc, ctx):
    rock, dark = sc((96, 76, 70)), sc((62, 48, 44))
    top = by - 620
    d.polygon([(cx - 620, by), (cx - 90, top), (cx + 90, top), (cx + 640, by)], fill=rock)
    d.polygon([(cx + 30, top), (cx + 90, top), (cx + 640, by), (cx + 220, by)], fill=dark)
    lava = (255, 120, 40) if ctx["time"] in ("night", "sunset") else (226, 96, 40)
    for dx, end in [(-30, 300), (40, 420), (-60, 220)]:
        d.line([(cx + dx, top + 6), (cx + dx * 2.2, top + end * 0.5), (cx + dx * 3.5, top + end)], fill=lava, width=10)
    d.ellipse([cx - 92, top - 16, cx + 92, top + 16], fill=(255, 150, 60))
    ctx["anchors"]["smoke"] = (cx, top - 10)
    # Roman ruins in front
    col = sc((222, 214, 196))
    for i, h in enumerate([150, 210, 90, 190, 130]):
        x = cx - 420 + i * 70
        d.rectangle([x, by + 40 - h, x + 34, by + 40], fill=col)

def lm_petra(img, d, cx, by, sc, ctx):
    rockc, rockd = sc((206, 120, 100)), sc((150, 82, 70))
    lit, dark = sc((226, 150, 124)), sc((168, 98, 82))
    xs, ys = ridge(img.width, 180, 120, 7, jag=True)
    d.polygon(list(zip(xs, ys)) + [(img.width, by + 60), (0, by + 60)], fill=rockc)
    for x in range(0, img.width, 90):
        d.line([(x, 260 + (x * 7) % 120), (x + 40, by)], fill=rockd, width=6)
    fx0, fx1 = cx - 330, cx + 330
    d.rectangle([fx0 - 40, by - 980, fx1 + 40, by + 40], fill=dark)   # niche
    # lower storey
    d.rectangle([fx0, by - 70, fx1, by], fill=lit)
    for i in range(6):
        x = fx0 + 40 + (fx1 - fx0 - 80) * i / 5
        d.rectangle([x - 22, by - 380, x + 22, by - 70], fill=lit)
        d.rectangle([x + 6, by - 380, x + 22, by - 70], fill=dark)
    d.rectangle([cx - 46, by - 260, cx + 46, by - 70], fill=sc((70, 36, 30)))
    d.rectangle([fx0, by - 440, fx1, by - 380], fill=lit)
    d.polygon([(cx - 200, by - 440), (cx, by - 540), (cx + 200, by - 440)], fill=lit)
    # upper storey with tholos
    y2 = by - 560
    for x in (fx0 + 30, fx0 + 110, fx1 - 110, fx1 - 30):
        d.rectangle([x - 20, y2 - 300, x + 20, y2], fill=lit)
    d.rectangle([cx - 110, y2 - 300, cx + 110, y2], fill=lit)
    for x in (cx - 80, cx, cx + 80):
        d.rectangle([x - 16, y2 - 290, x + 16, y2], fill=dark)
    d.polygon([(cx - 120, y2 - 300), (cx, y2 - 400), (cx + 120, y2 - 300)], fill=lit)
    d.ellipse([cx - 30, y2 - 450, cx + 30, y2 - 390], fill=lit)

def lm_terraces(img, d, cx, by, sc, ctx):
    peak, peakd = sc((52, 104, 70)), sc((34, 78, 52))
    d.polygon([(cx + 80, by), (cx + 300, by - 760), (cx + 360, by - 800), (cx + 430, by - 720), (cx + 700, by)], fill=peak)
    d.polygon([(cx + 360, by - 800), (cx + 430, by - 720), (cx + 700, by), (cx + 450, by)], fill=peakd)
    green, edge = sc((112, 170, 92)), sc((150, 140, 120))
    for i in range(7):
        y = by - i * 36
        w = 900 - i * 70
        d.rectangle([cx - w / 2 - 200, y - 36, cx - w / 2 - 200 + w * 0.7, y], fill=green)
        d.rectangle([cx - w / 2 - 200, y - 8, cx - w / 2 - 200 + w * 0.7, y], fill=edge)
    wall, roof = sc((186, 178, 164)), sc((130, 100, 70))
    for i, x in enumerate(range(int(cx - 380), int(cx + 60), 76)):
        y = by - 252 - (i % 3) * 18
        d.rectangle([x, y - 50, x + 60, y], fill=wall)
        d.polygon([(x - 6, y - 50), (x + 30, y - 86), (x + 66, y - 50)], fill=roof)

def lm_pisa(img, d, cx, by, sc, ctx):
    lit, dark, arch = sc((240, 236, 226)), sc((196, 190, 178)), sc((150, 146, 140))
    tw, th = 230, 680
    t = Image.new("RGBA", (tw + 80, th + 80), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    x0 = 40
    td.rectangle([x0, 80, x0 + tw, th + 80], fill=lit)
    td.rectangle([x0 + tw * 0.62, 80, x0 + tw, th + 80], fill=dark)
    for k in range(8):
        y = th + 80 - (k + 1) * (th / 8.6)
        td.rectangle([x0 - 8, y - 6, x0 + tw + 8, y + 4], fill=dark)
        for a in range(5):
            ax = x0 + 18 + a * (tw - 36) / 4
            td.rounded_rectangle([ax - 12, y + 12, ax + 12, y + 60], 12, fill=arch)
    td.rectangle([x0 + 30, 20, x0 + tw - 30, 90], fill=lit)
    td.rectangle([x0 + tw * 0.6, 20, x0 + tw - 30, 90], fill=dark)
    t = t.rotate(-5.5, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(t, (int(cx - t.width / 2 + 40), int(by - t.height + 30)))
    d.rectangle([cx - 520, by - 160, cx - 200, by], fill=lit)   # cathedral hint
    d.polygon([(cx - 540, by - 160), (cx - 360, by - 260), (cx - 180, by - 160)], fill=dark)

def lm_dome(img, d, cx, by, sc, ctx, style="taj"):
    if style == "taj":
        lit, dark, domec = sc((246, 243, 238)), sc((204, 200, 194)), sc((250, 248, 244))
    else:
        lit, dark, domec = sc((214, 166, 146)), sc((168, 120, 104)), sc((128, 138, 160))
    d.rectangle([cx - 520, by - 50, cx + 520, by], fill=dark)
    d.rectangle([cx - 300, by - 380, cx + 300, by - 50], fill=lit)
    d.rectangle([cx + 120, by - 380, cx + 300, by - 50], fill=dark)
    d.rounded_rectangle([cx - 90, by - 330, cx + 90, by - 50], 90, fill=sc((150, 140, 136)))
    if style == "taj":
        d.ellipse([cx - 210, by - 720, cx + 210, by - 330], fill=domec)
        d.polygon([(cx - 40, by - 700), (cx, by - 800), (cx + 40, by - 700)], fill=domec)
        d.rectangle([cx - 4, by - 860, cx + 4, by - 790], fill=sc((210, 180, 90)))
        for dx in (-230, 230):
            d.rectangle([cx + dx - 40, by - 460, cx + dx + 40, by - 380], fill=lit)
            d.ellipse([cx + dx - 46, by - 520, cx + dx + 46, by - 430], fill=domec)
        for dx in (-470, 470):
            d.polygon([(cx + dx - 26, by - 50), (cx + dx - 18, by - 600), (cx + dx + 18, by - 600), (cx + dx + 26, by - 50)], fill=lit)
            d.ellipse([cx + dx - 32, by - 650, cx + dx + 32, by - 590], fill=domec)
    else:
        d.pieslice([cx - 330, by - 640, cx + 330, by - 300], 180, 360, fill=domec)
        for dx in (-330, 330):
            d.pieslice([cx + dx - 170, by - 520, cx + dx + 170, by - 300], 180, 360, fill=domec)
        for k in range(14):
            x = cx - 290 + k * 44
            d.rectangle([x, by - 486, x + 16, by - 462], fill=sc((250, 230, 170)))
        for dx in (-480, 480):
            d.rectangle([cx + dx - 18, by - 620, cx + dx + 18, by - 50], fill=lit)
            d.polygon([(cx + dx - 20, by - 620), (cx + dx, by - 720), (cx + dx + 20, by - 620)], fill=domec)

def lm_madrasa(img, d, cx, by, sc, ctx):
    tan, tand = sc((214, 184, 142)), sc((170, 140, 104))
    blue, turq, gold = sc((38, 96, 180)), sc((56, 170, 192)), sc((222, 176, 70))
    def portal(x, w, h, dome_side):
        if dome_side:
            ddx = x + dome_side * (w * 0.75)
            d.rectangle([ddx - 90, by - h + 40, ddx + 90, by - h + 140], fill=tan)
            d.ellipse([ddx - 120, by - h - 140, ddx + 120, by - h + 80], fill=turq)
            for k in range(-3, 4):
                d.line([(ddx + k * 30, by - h - 120 + abs(k) * 12), (ddx + k * 34, by - h + 70)], fill=blue, width=4)
        d.rectangle([x - w / 2 - 120, by - h * 0.55, x + w / 2 + 120, by], fill=tand)
        d.rectangle([x - w / 2, by - h, x + w / 2, by], fill=tan)
        d.rectangle([x - w / 2 + 20, by - h + 20, x + w / 2 - 20, by], fill=blue)
        d.pieslice([x - w / 2 + 50, by - h + 60, x + w / 2 - 50, by - h + 60 + (w - 100)], 180, 360, fill=sc((26, 48, 96)))
        d.rectangle([x - w / 2 + 50, by - h + 60 + (w - 100) / 2 - 1, x + w / 2 - 50, by], fill=sc((26, 48, 96)))
        for yy in range(int(by - h + 40), int(by), 44):
            for xx in (x - w / 2 + 32, x + w / 2 - 32):
                d.regular_polygon((xx, yy, 9), 4, fill=gold)
        for mx in (x - w / 2 - 110, x + w / 2 + 110):
            d.rectangle([mx - 22, by - h - 40, mx + 22, by], fill=tan)
            for yy in range(int(by - h), int(by), 50):
                d.rectangle([mx - 22, yy, mx + 22, yy + 12], fill=blue)
            d.ellipse([mx - 28, by - h - 66, mx + 28, by - h - 20], fill=turq)
    portal(cx - 470, 200, 420, -1)
    portal(cx + 470, 200, 420, 1)
    portal(cx, 250, 470, 0)

def lm_soldiers(img, d, cx, by, sc, ctx):
    earth, earthd = sc((150, 110, 80)), sc((118, 84, 60))
    d.rectangle([0, by - 260, img.width, by + 200], fill=earthd)
    for r in range(5):
        k = r / 4.0
        y = by - 200 + k * 300
        s = 0.55 + k * 0.6
        body, bodyd = sc(mix((200, 160, 128), (176, 112, 78), k)), sc(mix((160, 124, 98), (128, 80, 54), k))
        d.rectangle([0, y + 6 * s, img.width, y + 26 * s], fill=earth)
        n = int(16 - r * 2)
        for i in range(n):
            x = cx - 520 * s + (1040 * s) * i / (n - 1)
            d.rectangle([x - 22 * s, y - 120 * s, x + 22 * s, y], fill=body)
            d.rectangle([x + 4 * s, y - 120 * s, x + 22 * s, y], fill=bodyd)
            d.ellipse([x - 16 * s, y - 158 * s, x + 16 * s, y - 120 * s], fill=body)
            d.rectangle([x - 12 * s, y - 166 * s, x + 12 * s, y - 150 * s], fill=bodyd)

def lm_gardens(img, d, cx, by, sc, ctx):
    brick, brickd = sc((196, 152, 100)), sc((150, 110, 70))
    leaf, leafd = sc((76, 150, 72)), sc((44, 110, 52))
    for i in range(5):
        w = 900 - i * 160
        y1 = by - i * 110
        d.rectangle([cx - w / 2, y1 - 110, cx + w / 2, y1], fill=brick)
        d.rectangle([cx + w * 0.2, y1 - 110, cx + w / 2, y1], fill=brickd)
        for k in range(int(w // 46)):
            x = cx - w / 2 + 23 + k * 46
            d.ellipse([x - 30, y1 - 140, x + 30, y1 - 92], fill=leaf if k % 2 else leafd)
            d.line([(x, y1 - 96), (x + 4, y1 - 40)], fill=leafd, width=6)
        d.line([(cx - w / 2 + 40, y1 - 100), (cx - w / 2 + 40, y1)], fill=sc((150, 210, 240)), width=8)
    for dx in (-60, 60):
        d.rectangle([cx + dx - 6, by - 700, cx + dx + 6, by - 550], fill=sc((110, 80, 50)))
        d.ellipse([cx + dx - 70, by - 760, cx + dx + 70, by - 660], fill=leaf)

def lm_tpillars(img, d, cx, by, sc, ctx):
    lit, dark, wall = sc((214, 204, 178)), sc((164, 154, 132)), sc((150, 136, 110))
    d.ellipse([cx - 560, by - 90, cx + 560, by + 80], fill=wall)
    d.ellipse([cx - 500, by - 60, cx + 500, by + 60], fill=sc((176, 160, 124)))
    for x, s in [(-420, 0.7), (-250, 0.85), (250, 0.85), (420, 0.7), (-70, 1.15), (110, 1.15)]:
        X = cx + x
        w, h = 56 * s, 300 * s
        d.rectangle([X - w / 2, by - h, X + w / 2, by], fill=lit)
        d.rectangle([X + w * 0.1, by - h, X + w / 2, by], fill=dark)
        d.rectangle([X - w * 1.4, by - h - 60 * s, X + w * 1.5, by - h + 4], fill=lit)
        d.rectangle([X + w * 0.4, by - h - 60 * s, X + w * 1.5, by - h + 4], fill=dark)
        d.line([(X - 14 * s, by - h + 60 * s), (X - 6 * s, by - h + 120 * s), (X + 8 * s, by - h + 100 * s)], fill=dark, width=4)

def lm_nazca(img, d, cx, by, sc, ctx):
    t = Image.new("RGBA", (1400, 1400), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    c = sc((246, 226, 196)) + (255,)
    # stylised hummingbird
    td.line([(700, 200), (700, 1000)], fill=c, width=16)
    td.line([(700, 1000), (640, 1200), (700, 1120), (760, 1200), (700, 1000)], fill=c, width=14)
    td.line([(700, 520), (220, 330), (260, 420), (700, 600)], fill=c, width=14)
    td.line([(700, 520), (1180, 330), (1140, 420), (700, 600)], fill=c, width=14)
    td.line([(700, 200), (700, 60)], fill=c, width=10)
    for k in range(6):
        r = 40 + k * 26
        td.arc([1150 - r, 900 - r, 1150 + r, 900 + r], 0, 300, fill=c, width=10)
    td.line([(80, 1300), (1320, 1240)], fill=c, width=8)
    t = t.resize((1400, 420), Image.BICUBIC)
    img.alpha_composite(t, (int(cx - 700), int(by + 40)))

def lm_bricks(img, d, cx, by, sc, ctx):
    lit, dark = sc((190, 122, 82)), sc((140, 86, 56))
    d.pieslice([cx + 120, by - 380, cx + 520, by - 40], 180, 360, fill=lit)      # stupa mound
    d.rectangle([cx + 120, by - 210, cx + 520, by - 40], fill=lit)
    for r in range(3):
        y = by - 30 + r * 70
        s = 0.8 + r * 0.25
        for i in range(-5, 6):
            x = cx + i * 110 * s
            h = (60 + ((i * 37 + r * 11) % 5) * 14) * s
            d.rectangle([x - 44 * s, y - h, x + 44 * s, y], fill=lit)
            d.rectangle([x + 18 * s, y - h, x + 44 * s, y], fill=dark)
            d.rectangle([x - 12 * s, y - h * 0.6, x + 2 * s, y - h * 0.3], fill=sc((70, 44, 30)))
    d.rectangle([cx - 200, by + 170, cx + 200, by + 250], fill=dark)
    d.rectangle([cx - 180, by + 180, cx + 180, by + 240], fill=sc((70, 150, 190)))

def lm_cave(img, d, cx, by, sc, ctx):
    earth, earthd, room = sc((150, 112, 82)), sc((118, 86, 62)), (54, 36, 28)
    d.rectangle([0, by - 20, img.width, H], fill=earth)
    for y in range(int(by + 60), H, 70):
        d.line([(0, y), (img.width, y + 20)], fill=earthd, width=6)
    rooms = [(cx - 300, by + 140), (cx + 200, by + 230), (cx - 150, by + 380), (cx + 350, by + 470), (cx - 380, by + 560)]
    d.line([(cx - 60, by - 20), (cx - 60, by + 600)], fill=room, width=40)   # air shaft
    for (x1, y1), (x2, y2) in zip(rooms, rooms[1:]):
        d.line([(x1, y1), (x2, y2)], fill=room, width=46)
    for x, y in rooms:
        d.rounded_rectangle([x - 130, y - 60, x + 130, y + 60], 40, fill=room)
        d.ellipse([x - 40, y - 40, x + 40, y + 40], fill=(255, 170, 70, 110))
        d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(255, 220, 140))
    d.ellipse([cx + 360, by + 110, cx + 460, by + 210], fill=sc((150, 146, 140)))   # rolling stone door
    d.ellipse([cx + 400, by + 150, cx + 420, by + 170], fill=sc((100, 96, 90)))
    for dx in (-400, -200, 260):
        d.rectangle([cx + dx, by - 110, cx + dx + 90, by - 20], fill=sc((200, 176, 140)))

def lm_causeway(img, d, cx, by, sc, ctx):
    top, side = sc((84, 84, 90)), sc((46, 46, 52))
    rnd = random.Random(3)
    for row in range(6):
        y0 = by - 40 + row * 70
        s = 0.7 + row * 0.18
        for i in range(-8, 9):
            x = cx - 200 + i * 62 * s + (row % 2) * 31 * s
            h = (40 + rnd.randint(0, 120) + (8 - abs(i)) * 6) * s
            r = 34 * s
            d.rectangle([x - r, y0 - h, x + r, y0 + 40], fill=side)
            pts = [(x + r * math.cos(a), y0 - h + r * 0.45 * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)]]
            d.polygon(pts, fill=top)
    d.polygon([(0, by - 260), (380, by - 300), (520, by - 60), (0, by)], fill=sc((70, 92, 70)))

def lm_canyon(img, d, cx, by, sc, ctx):
    bands = [sc((198, 102, 64)), sc((226, 150, 96)), sc((170, 80, 50)), sc((214, 128, 80)), sc((150, 66, 42)), sc((120, 54, 36))]
    top, bh = by - 560, 120
    for side in (-1, 1):
        for k, c in enumerate(bands):
            y = top + k * bh
            i0 = cx + side * (420 - k * 60)
            i1 = cx + side * (420 - (k + 1) * 60)
            outer = cx + side * 1400
            d.polygon([(outer, y), (i0, y), (i1 + side * 18, y + bh), (outer, y + bh)], fill=c)
            d.line([(i0, y), (i1 + side * 18, y + bh)], fill=dk(c, 0.8), width=6)
    yb = top + len(bands) * bh
    d.rectangle([0, yb, img.width, H], fill=dk(bands[-1], 0.85))
    d.polygon([(cx - 70, yb - 40), (cx + 70, yb - 40), (cx + 110, yb + 30), (cx - 110, yb + 30)], fill=sc((60, 140, 160)))

def lm_pines(img, d, cx, by, sc, ctx):
    g = ctx["ground"]
    rnd = random.Random(11)
    for x in range(30, img.width, 70):
        if rnd.random() < 0.35:
            continue
        y = g(x) + 10
        h = rnd.randint(150, 300)
        d.polygon([(x - h * 0.28, y), (x, y - h), (x + h * 0.28, y)], fill=sc((20, 50, 44)))
        d.polygon([(x - h * 0.16, y - h * 0.45), (x, y - h), (x + h * 0.12, y - h * 0.5)], fill=sc((236, 240, 248)))
    d.rectangle([cx - 90, by - 110, cx + 90, by], fill=sc((110, 70, 44)))
    d.polygon([(cx - 120, by - 110), (cx, by - 200), (cx + 120, by - 110)], fill=sc((236, 240, 248)))
    d.rectangle([cx - 30, by - 70, cx + 10, by - 30], fill=(255, 210, 120))

def _mammoth(d, x, by, s, fur, furd, tusk):
    d.ellipse([x - 170 * s, by - 290 * s, x + 150 * s, by - 80 * s], fill=fur)
    d.ellipse([x - 190 * s, by - 340 * s, x - 10 * s, by - 170 * s], fill=fur)       # hump
    for lx in (-140, -80, 50, 100):
        d.rectangle([x + lx * s, by - 140 * s, x + (lx + 46) * s, by], fill=furd)
    d.ellipse([x + 80 * s, by - 330 * s, x + 230 * s, by - 180 * s], fill=fur)        # head
    d.line([(x + 210 * s, by - 220 * s), (x + 250 * s, by - 120 * s), (x + 230 * s, by - 40 * s)], fill=furd, width=int(30 * s), joint="curve")
    d.arc([x + 150 * s, by - 250 * s, x + 330 * s, by - 90 * s], 90, 250, fill=tusk, width=int(14 * s))

def lm_mammoths(img, d, cx, by, sc, ctx):
    fur, furd, tusk = sc((122, 78, 46)), sc((88, 54, 32)), sc((246, 238, 220))
    _mammoth(d, cx - 300, by + 10, 0.75, fur, furd, tusk)
    _mammoth(d, cx + 120, by + 40, 1.0, fur, furd, tusk)

def lm_acacia(img, d, cx, by, sc, ctx):
    d.ellipse([cx - 420, by - 30, cx + 380, by + 110], fill=sc((70, 150, 200)))
    trunk, leaf = sc((96, 70, 46)), sc((70, 128, 56))
    for x, s in [(-460, 0.8), (430, 1.0), (180, 0.6)]:
        X = cx + x
        d.line([(X, by), (X + 10 * s, by - 220 * s), (X - 30 * s, by - 300 * s)], fill=trunk, width=int(22 * s))
        d.line([(X + 10 * s, by - 220 * s), (X + 70 * s, by - 290 * s)], fill=trunk, width=int(16 * s))
        d.ellipse([X - 170 * s, by - 350 * s, X + 170 * s, by - 270 * s], fill=leaf)
    # giraffe
    gx, gc = cx - 160, sc((214, 160, 80))
    d.rectangle([gx - 60, by - 220, gx + 70, by - 150], fill=gc)
    for lx in (-55, -30, 40, 60):
        d.rectangle([gx + lx, by - 160, gx + lx + 10, by - 20], fill=gc)
    d.line([(gx + 60, by - 210), (gx + 120, by - 380)], fill=gc, width=24)
    d.ellipse([gx + 100, by - 410, gx + 160, by - 370], fill=gc)

def lm_rockart(img, d, cx, by, sc, ctx):
    rock, rockd, ochre = sc((176, 120, 80)), sc((136, 90, 60)), sc((150, 50, 30))
    d.polygon([(cx - 480, by + 40), (cx - 430, by - 420), (cx - 100, by - 500), (cx + 300, by - 460), (cx + 480, by - 200), (cx + 500, by + 40)], fill=rock)
    d.polygon([(cx + 300, by - 460), (cx + 480, by - 200), (cx + 500, by + 40), (cx + 260, by + 40)], fill=rockd)
    def giraffe(x, y, s):
        d.line([(x, y), (x + 60 * s, y)], fill=ochre, width=8)
        for lx in (0, 60):
            d.line([(x + lx * s, y), (x + lx * s, y + 70 * s)], fill=ochre, width=6)
        d.line([(x + 60 * s, y), (x + 100 * s, y - 100 * s)], fill=ochre, width=7)
    giraffe(cx - 300, by - 300, 1.2)
    giraffe(cx - 60, by - 260, 0.9)
    for k in range(3):
        x = cx + 120 + k * 50
        d.ellipse([x - 10, by - 220, x + 10, by - 200], fill=ochre)
        d.line([(x, by - 200), (x, by - 150), (x - 14, by - 110)], fill=ochre, width=6)
        d.line([(x, by - 150), (x + 14, by - 110)], fill=ochre, width=6)
        d.line([(x - 20, by - 180), (x + 20, by - 170)], fill=ochre, width=5)

def lm_stadium(img, d, cx, by, sc, ctx):
    d.polygon([(0, by - 30), (img.width, by - 30), (img.width, by + 200), (0, by + 200)], fill=sc((120, 160, 90)))
    d.polygon([(cx - 600, by + 20), (cx + 600, by + 20), (cx + 800, by + 220), (cx - 800, by + 220)], fill=sc((220, 186, 132)))
    for k in range(4):
        d.line([(cx - 600 - k * 40, by + 40 + k * 50), (cx + 600 + k * 40, by + 40 + k * 50)], fill=sc((246, 232, 200)), width=4)
    lit, dark = sc((236, 228, 212)), sc((190, 182, 166))
    for i in range(6):
        x = cx - 300 + i * 120
        d.rectangle([x - 20, by - 300, x + 20, by - 30], fill=lit)
        d.rectangle([x + 6, by - 300, x + 20, by - 30], fill=dark)
    d.rectangle([cx - 340, by - 340, cx + 340, by - 300], fill=lit)

LANDMARKS = {
    "pyramids": lm_pyramids, "sphinx": lm_sphinx, "stonehenge": lm_stonehenge, "temple": lm_temple,
    "colosseum": lm_colosseum, "greatwall": lm_greatwall, "moai": lm_moai, "mayan": lm_mayan,
    "angkor": lm_angkor, "lighthouse": lm_lighthouse, "volcano": lm_volcano, "petra": lm_petra,
    "terraces": lm_terraces, "pisa": lm_pisa, "taj": lambda *a: lm_dome(*a, style="taj"),
    "hagia": lambda *a: lm_dome(*a, style="hagia"), "madrasa": lm_madrasa, "soldiers": lm_soldiers,
    "gardens": lm_gardens, "tpillars": lm_tpillars, "nazca": lm_nazca, "bricks": lm_bricks,
    "cave": lm_cave, "causeway": lm_causeway, "canyon": lm_canyon, "pines": lm_pines,
    "mammoths": lm_mammoths, "acacia": lm_acacia, "rockart": lm_rockart, "stadium": lm_stadium,
    "none": lambda *a: None,
}

# ---------------------------------------------------------------- effects
class FX:
    """Animated particles. stage 'back' = behind landscape, 'front' = in front."""
    def __init__(self, kind, rnd, ctx, pal):
        self.kind, self.ctx, self.pal = kind, ctx, pal
        self.stage = "back" if kind in ("stars", "clouds", "aurora", "gear", "birds") else "front"
        r = rnd
        if kind == "stars":
            self.p = [(r.uniform(0, W), r.uniform(0, HORIZON - 150), r.uniform(1.5, 4.2), r.uniform(0, 6.28)) for _ in range(150)]
        elif kind == "clouds":
            self.p = []
            tint = mix((255, 255, 255), pal["bot"], 0.35)
            for _ in range(4):
                cw, chh = r.randint(380, 640), r.randint(110, 170)
                im = Image.new("RGBA", (cw + 80, chh + 80), (0, 0, 0, 0))
                cd = ImageDraw.Draw(im)
                for _ in range(9):
                    bx, bw = r.uniform(40, cw - 120), r.uniform(120, 240)
                    bh = r.uniform(70, chh)
                    cd.ellipse([bx, 40 + chh - bh, bx + bw, 40 + chh], fill=tint + (200,))
                im = im.filter(ImageFilter.GaussianBlur(6))
                self.p.append([im, r.uniform(-300, W), r.uniform(120, HORIZON - 420), r.uniform(8, 22)])
        elif kind == "birds":
            self.p = [(r.uniform(-200, W), r.uniform(250, HORIZON - 300), r.uniform(40, 80), r.uniform(0, 6.28), r.uniform(0.7, 1.2)) for _ in range(5)]
        elif kind == "dust":
            self.p = [(r.uniform(0, W), r.uniform(HORIZON - 400, H), r.uniform(2, 6), r.uniform(10, 40), r.uniform(0, 6.28)) for _ in range(70)]
        elif kind == "snow":
            self.p = [(r.uniform(0, W), r.uniform(0, H), r.uniform(3, 8), r.uniform(60, 140), r.uniform(0, 6.28)) for _ in range(140)]
        elif kind == "fireflies":
            self.p = [(r.uniform(0, W), r.uniform(HORIZON - 200, H - 200), r.uniform(0, 6.28), r.uniform(0.5, 1.4)) for _ in range(40)]
        elif kind == "waves":
            self.p = [(r.uniform(0, W), r.uniform(HORIZON + 20, H), r.uniform(0, 6.28)) for _ in range(160)]
        elif kind == "smoke":
            self.p = [(r.uniform(0, 1), r.uniform(-40, 40)) for _ in range(26)]
        elif kind == "aurora":
            im = Image.new("RGBA", (W * 2, 900), (0, 0, 0, 0))
            ad = ImageDraw.Draw(im)
            for band, col in enumerate([(80, 255, 170), (120, 255, 200), (200, 120, 255)]):
                pts = []
                for x in range(0, W * 2 + 20, 20):
                    y = 380 + band * 90 + 120 * math.sin(x / 260 + band) + 50 * math.sin(x / 90 + band * 2)
                    pts.append((x, y))
                for k in range(16):
                    ad.line([(x, y - k * 14) for x, y in pts], fill=col + (max(0, 70 - k * 4),), width=16)
            self.img = im.filter(ImageFilter.GaussianBlur(14))
        elif kind == "gear":
            self.gears = []
            for size, teeth in [(560, 24), (300, 14)]:
                g = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                gd = ImageDraw.Draw(g)
                c, rr = size / 2, size / 2 - 30
                col = (206, 156, 78, 235)
                for t in range(teeth):
                    a = 2 * math.pi * t / teeth
                    pts = [(c + (rr - 4) * math.cos(a - 0.09), c + (rr - 4) * math.sin(a - 0.09)),
                           (c + (rr + 26) * math.cos(a - 0.05), c + (rr + 26) * math.sin(a - 0.05)),
                           (c + (rr + 26) * math.cos(a + 0.05), c + (rr + 26) * math.sin(a + 0.05)),
                           (c + (rr - 4) * math.cos(a + 0.09), c + (rr - 4) * math.sin(a + 0.09))]
                    gd.polygon(pts, fill=col)
                gd.ellipse([c - rr, c - rr, c + rr, c + rr], fill=col)
                gd.ellipse([c - rr * 0.78, c - rr * 0.78, c + rr * 0.78, c + rr * 0.78], fill=(150, 108, 50, 235))
                for s in range(4):
                    a = s * math.pi / 2
                    gd.line([(c, c), (c + rr * 0.8 * math.cos(a), c + rr * 0.8 * math.sin(a))], fill=col, width=int(size * 0.07))
                gd.ellipse([c - rr * 0.18, c - rr * 0.18, c + rr * 0.18, c + rr * 0.18], fill=col)
                self.gears.append((g, teeth))

    def draw(self, frame, d, t, offs):
        k = self.kind
        if k == "stars":
            for x, y, rr, ph in self.p:
                a = int(120 + 120 * (0.5 + 0.5 * math.sin(t * 2.2 + ph)))
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 240, a))
        elif k == "clouds":
            for im, x0, y, sp in self.p:
                x = (x0 + sp * t) % (W + 700) - 650
                frame.paste(im, (int(x), int(y)), im)
        elif k == "birds":
            for x0, y0, sp, ph, s in self.p:
                x = (x0 + sp * t) % (W + 300) - 150
                y = y0 + 10 * math.sin(t + ph)
                f = math.sin(t * 7 + ph) * 12 * s
                col = (40, 40, 50, 210) if self.ctx["time"] != "night" else (220, 220, 240, 160)
                d.line([(x - 22 * s, y - f), (x, y), (x + 22 * s, y - f)], fill=col, width=4)
        elif k == "dust":
            for x0, y0, rr, sp, ph in self.p:
                x = (x0 + sp * t) % W
                y = y0 - 8 * t + 10 * math.sin(t + ph)
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 236, 200, 70))
        elif k == "snow":
            for x0, y0, rr, sp, ph in self.p:
                y = (y0 + sp * t) % H
                x = x0 + 30 * math.sin(t * 0.8 + ph)
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255, 200))
        elif k == "fireflies":
            for x0, y0, ph, sp in self.p:
                x = x0 + 40 * math.sin(t * sp + ph)
                y = y0 + 30 * math.cos(t * sp * 0.8 + ph)
                a = int(140 * (0.5 + 0.5 * math.sin(t * 3 + ph)))
                d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(230, 255, 120, a // 4))
                d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(250, 255, 180, a + 80))
        elif k == "waves":
            for x0, y0, ph in self.p:
                persp = (y0 - HORIZON) / (H - HORIZON)
                ln = 14 + 60 * persp
                x = (x0 + 18 * math.sin(t * 1.3 + ph) - offs[1]) % W
                a = int(60 + 120 * (0.5 + 0.5 * math.sin(t * 2 + ph)))
                d.line([(x, y0), (x + ln, y0)], fill=(230, 245, 255, a), width=max(2, int(5 * persp)))
        elif k == "smoke":
            ax, ay = self.ctx["anchors"].get("smoke", (W / 2, HORIZON - 600))
            ax -= offs[1]
            for ph, dx in self.p:
                life = (t * 0.25 + ph) % 1.0
                rr = 40 + 160 * life
                x = ax + dx + 140 * life
                y = ay - 520 * life
                g = int(90 + 60 * life)
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(g, g, g, int(150 * (1 - life))))
        elif k == "beam":
            ax, ay = self.ctx["anchors"].get("beam", (W / 2, HORIZON - 700))
            ax -= offs[1]
            a = t * 1.4
            for sign in (1, -1):
                ang = a + (0 if sign > 0 else math.pi)
                L = 1400
                p1 = (ax + L * math.cos(ang - 0.08), ay + L * 0.25 * math.sin(ang - 0.08))
                p2 = (ax + L * math.cos(ang + 0.08), ay + L * 0.25 * math.sin(ang + 0.08))
                d.polygon([(ax, ay), p1, p2], fill=(255, 240, 180, 60))
            d.ellipse([ax - 90, ay - 90, ax + 90, ay + 90], fill=(255, 210, 120, 70))
        elif k == "aurora":
            x = int(-W * 0.5 + 220 * math.sin(t * 0.25))
            frame.paste(self.img, (x, 60), self.img)
        elif k == "gear":
            (g1, t1), (g2, t2) = self.gears
            r1 = g1.rotate(t * 18, resample=Image.BICUBIC)
            r2 = g2.rotate(-t * 18 * t1 / t2 + 7, resample=Image.BICUBIC)
            frame.paste(r1, (W // 2 - 380, 330), r1)
            frame.paste(r2, (W // 2 + 120, 300), r2)

# ---------------------------------------------------------------- scene
SPEED = (8, 20, 46)   # parallax px/s for far, mid, near

class Scene:
    def __init__(self, spec, dur, seed):
        self.dur = dur
        time = spec.get("time", "day")
        terr = spec.get("terrain", "grass")
        pal = PAL[time]
        tc = TERRAIN[terr]
        rnd = random.Random(seed)
        self.zoom_in = rnd.random() < 0.7
        # sky
        sun = spec.get("sun", [0.72, 0.30])
        sx, sy = sun[0] * W, sun[1] * H
        if time == "sunset":
            sy = HORIZON - 260
        yy = np.linspace(0, 1, H)[:, None, None]
        top, bot = np.array(pal["top"], float), np.array(pal["bot"], float)
        img = top + (bot - top) * (yy ** 0.85)
        img = np.repeat(img, W, axis=1)
        gy, gx = np.mgrid[0:H, 0:W]
        dist = np.sqrt((gx - sx) ** 2 + (gy - sy) ** 2)
        glow = (np.exp(-(dist / 420.0) ** 2) * (0.75 if time != "day" else 0.45))[..., None]
        img = img + (np.array(pal["sun"], float) - img) * glow
        sky = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGB")
        sd = ImageDraw.Draw(sky)
        rr = 70 if time == "night" else 96
        sd.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=pal["sun"])
        if time == "night":
            for cx_, cy_, cr in [(-22, -18, 16), (20, 14, 11), (-6, 30, 8), (26, -24, 7)]:
                sd.ellipse([sx + cx_ - cr, sy + cy_ - cr, sx + cx_ + cr, sy + cy_ + cr], fill=(206, 210, 230))
        self.sky = sky

        ctx = {"anchors": {}, "time": time}
        self.ctx = ctx
        sc = lambda c: shade(c, pal, 0.08)
        layers = []
        # far
        fw = W + int(SPEED[0] * dur) + 60
        jag = terr in ("mountains", "snow", "canyon")
        xs, ys = ridge(fw, HORIZON - (150 if jag else 60), 380 if jag else 150, seed + 1, jag=jag)
        far = poly_layer(fw, xs, ys, shade(tc["far"], pal, 0.75))
        if terr == "jungle":
            fd = ImageDraw.Draw(far)
            for x in range(0, fw, 46):
                y = ridge_fn(xs, ys)(x)
                fd.ellipse([x - 40, y - 50, x + 40, y + 30], fill=shade(tc["far"], pal, 0.75))
        if terr == "sea":
            far = Image.new("RGBA", (fw, H), (0, 0, 0, 0))
            fd = ImageDraw.Draw(far)
            xs2, ys2 = ridge(fw, HORIZON - 30, 60, seed + 1)
            fd.polygon(list(zip(xs2, ys2)) + [(fw, HORIZON), (0, HORIZON)], fill=shade(tc["far"], pal, 0.8) + (255,))
        layers.append(crop_layer(far) + (SPEED[0],))
        # mid
        mw = W + int(SPEED[1] * dur) + 60
        mid = Image.new("RGBA", (mw, H), (0, 0, 0, 0))
        md = ImageDraw.Draw(mid)
        if terr == "sea":
            water = np.zeros((H - HORIZON, mw, 4), np.uint8)
            c1, c2 = np.array(shade(tc["mid"], pal, 0.3)), np.array(shade(tc["near"], pal, 0.0))
            ramp = np.linspace(0, 1, H - HORIZON)[:, None, None]
            water[..., :3] = (c1 + (c2 - c1) * ramp).astype(np.uint8)
            water[..., 3] = 255
            mid.paste(Image.fromarray(water, "RGBA"), (0, HORIZON))
            # sun reflection
            for y in range(HORIZON, H, 18):
                ww = 30 + (y - HORIZON) * 0.25
                md.line([(sx + SPEED[1] * dur / 2 - ww, y), (sx + SPEED[1] * dur / 2 + ww, y)], fill=pal["sun"] + (70,), width=6)
            ground = lambda x: HORIZON
        else:
            amp = 160 if spec.get("landmark") == "greatwall" else 40
            xs, ys = ridge(mw, HORIZON + 20, amp, seed + 2)
            md.polygon(list(zip(xs, ys)) + [(mw, H), (0, H)], fill=shade(tc["mid"], pal, 0.15) + (255,))
            ground = ridge_fn(xs, ys)
            if terr == "jungle":
                for x in range(0, mw, 60):
                    y = ground(x)
                    md.ellipse([x - 54, y - 70, x + 54, y + 20], fill=shade((52, 120, 70), pal, 0.15))
        ctx["ground"] = ground
        cx = W / 2 + SPEED[1] * dur / 2
        by = HORIZON + 30 + spec.get("dy", 0)
        LANDMARKS[spec.get("landmark", "none")](mid, ImageDraw.Draw(mid), cx, by, sc, ctx)
        if "beam" in ctx["anchors"]:
            pass
        layers.append(crop_layer(mid) + (SPEED[1],))
        # near
        if spec.get("near", terr not in ("sea",)) and spec.get("landmark") not in ("cave", "nazca", "soldiers", "causeway", "canyon"):
            nw = W + int(SPEED[2] * dur) + 60
            xs, ys = ridge(nw, int(H * 0.86), 90, seed + 3)
            near = poly_layer(nw, xs, ys, shade(tc["near"], pal, 0.0))
            nd = ImageDraw.Draw(near)
            gcol = dk(shade(tc["near"], pal, 0.0), 0.8)
            for x in range(0, nw, 22):
                y = ridge_fn(xs, ys)(x)
                h = rnd.randint(14, 46)
                nd.line([(x, y + 6), (x + rnd.randint(-8, 8), y - h)], fill=gcol, width=5)
            layers.append(crop_layer(near) + (SPEED[2],))
        self.layers = layers
        # effects
        fx = list(spec.get("fx", []))
        if time == "night" and "stars" not in fx:
            fx.insert(0, "stars")
        if time != "night" and "clouds" not in fx and terr != "canyon":
            fx.insert(0, "clouds")
        if time == "day" and "birds" not in fx and rnd.random() < 0.6:
            fx.append("birds")
        if terr == "sea" and "waves" not in fx:
            fx.append("waves")
        if terr == "desert" and "dust" not in fx:
            fx.append("dust")
        if terr == "snow" and "snow" not in fx:
            fx.append("snow")
        if "beam" in ctx["anchors"] and "beam" not in fx:
            fx.append("beam")
        if "smoke" in ctx["anchors"] and "smoke" not in fx:
            fx.append("smoke")
        self.fx = [FX(k, random.Random(seed + 10 + i), ctx, pal) for i, k in enumerate(fx)]

    def frame(self, t):
        f = self.sky.copy()
        d = ImageDraw.Draw(f, "RGBA")
        offs = [SPEED[i] * t for i in range(3)]
        for e in self.fx:
            if e.stage == "back":
                e.draw(f, d, t, offs)
        for i, (im, y0, sp) in enumerate(self.layers):
            f.paste(im, (-int(sp * t), y0), im)
            if i == 1:
                for e in self.fx:
                    if e.stage == "front" and e.kind in ("waves", "beam", "smoke"):
                        e.draw(f, d, t, offs)
        for e in self.fx:
            if e.stage == "front" and e.kind not in ("waves", "beam", "smoke"):
                e.draw(f, d, t, offs)
        p = t / max(self.dur, 0.01)
        z = 1.16 + 0.08 * (p if self.zoom_in else 1 - p)
        cw, ch = W / z, H / z
        x0 = (W - cw) / 2
        y0 = min(max(0.0, HORIZON - 330 - ch / 2), H - ch)
        return f.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))

# ---------------------------------------------------------------- text overlays
SUB_FONT = None

def chunk_words(words):
    """words: [(start, end, text)] -> chunks of up to 3 words, split on pauses."""
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        pause = nxt is not None and nxt[0] - w[1] > 0.18
        if len(cur) >= 3 or pause or nxt is None or w[2][-1:] in ".,!?;:":
            chunks.append(cur)
            cur = []
    return chunks

def render_chunk(words, active):
    global SUB_FONT
    if SUB_FONT is None:
        SUB_FONT = font(98)
    fnt = SUB_FONT
    space = fnt.getlength(" ")
    widths = [fnt.getlength(w[2]) for w in words]
    lines, cur, cw = [], [], 0
    for i, wd in enumerate(widths):
        if cur and cw + space + wd > 940:
            lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += wd + (space if len(cur) > 1 else 0)
    lines.append(cur)
    lh = 124
    im = Image.new("RGBA", (W, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, line in enumerate(lines):
        tw = sum(widths[i] for i in line) + space * (len(line) - 1)
        x = (W - tw) / 2
        for i in line:
            col = (255, 214, 64) if i == active else (255, 255, 255)
            d.text((x, 14 + li * lh), words[i][2], font=fnt, fill=col, stroke_width=10, stroke_fill=(10, 10, 20))
            x += widths[i] + space
    return im

def make_title(kicker, label):
    f1, f2 = font(52), font(84)
    lines, cur = [], ""
    for word in label.split():
        test = (cur + " " + word).strip()
        if f2.getlength(test) > 900 and cur:
            lines.append(cur); cur = word
        else:
            cur = test
    lines.append(cur)
    h = 110 + 100 * len(lines)
    im = Image.new("RGBA", (W, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bw = max(f2.getlength(l) for l in lines) + 100
    d.rounded_rectangle([(W - bw) / 2, 0, (W + bw) / 2, h], 40, fill=(12, 14, 30, 200))
    d.text((W / 2, 50), kicker, font=f1, fill=(255, 214, 64), anchor="mm")
    for i, l in enumerate(lines):
        d.text((W / 2, 140 + i * 100), l, font=f2, fill=(255, 255, 255), anchor="mm")
    return im

def make_vignette():
    gy, gx = np.mgrid[0:H, 0:W]
    dx, dy = (gx - W / 2) / (W / 2), (gy - H / 2) / (H / 2)
    r = np.sqrt(dx ** 2 * 0.8 + dy ** 2)
    a = np.clip((r - 0.75) * 260, 0, 150).astype(np.uint8)
    top = np.clip((1 - gy / 520.0) * 90, 0, 90).astype(np.uint8)
    a = np.maximum(a, top)
    v = np.zeros((H, W, 4), np.uint8)
    v[..., 3] = a
    return Image.fromarray(v, "RGBA")

# ---------------------------------------------------------------- audio
async def _tts(text, mp3):
    import edge_tts
    try:
        com = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
    except TypeError:
        com = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    words = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s = ch["offset"] / 1e7
                words.append((s, s + ch["duration"] / 1e7, ch["text"]))
    return words

def attach_punct(words, text):
    """Edge TTS word boundaries drop punctuation; copy it back from the script."""
    toks = text.split()
    out, j = [], 0
    for s, e, w in words:
        key = "".join(ch for ch in w.lower() if ch.isalnum())
        disp = w
        for k in range(j, min(j + 4, len(toks))):
            tk = "".join(ch for ch in toks[k].lower() if ch.isalnum())
            if tk and (tk == key or tk.startswith(key) or key.startswith(tk)):
                disp, j = toks[k], k + 1
                break
        out.append((s, e, disp))
    return out

def estimate_words(text):
    t, out = 0.0, []
    for w in text.split():
        d = 0.16 + 0.055 * len(w)
        out.append((t, t + d, w))
        t += d + (0.32 if w[-1] in ".!?" else 0.14 if w[-1] in ",;:" else 0.02)
    return out

def duration_of(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

def make_music(path, dur, seed=0):
    sr = 44100
    n = int(sr * dur)
    t = np.arange(n) / sr
    rnd = random.Random(seed)
    progs = [[[220.0, 277.18, 329.63], [196.0, 246.94, 293.66], [174.61, 220.0, 261.63], [196.0, 246.94, 329.63]],
             [[261.63, 329.63, 392.0], [220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 246.94, 293.66]],
             [[146.83, 220.0, 293.66], [174.61, 220.0, 261.63], [130.81, 196.0, 261.63], [196.0, 246.94, 293.66]]]
    prog = progs[seed % len(progs)]
    seg = 4.0
    out = np.zeros(n)
    for i in range(int(dur / seg) + 2):
        chord = prog[i % len(prog)]
        s0 = int(i * seg * sr)
        if s0 >= n:
            break
        L = min(n - s0, int((seg + 1.0) * sr))
        tt = np.arange(L) / sr
        env = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (seg + 1.0 - tt) / 1.2))
        for fr in chord:
            out[s0:s0 + L] += env * (np.sin(2 * np.pi * fr / 2 * tt) * 0.5 + 0.15 * np.sin(2 * np.pi * fr * tt))
        for b in range(8):                                   # soft bell arpeggio
            bs = s0 + int(b * 0.5 * sr)
            if bs >= n:
                break
            fr = chord[rnd.randrange(3)] * 2
            BL = min(n - bs, int(1.6 * sr))
            bt = np.arange(BL) / sr
            out[bs:bs + BL] += 0.22 * np.sin(2 * np.pi * fr * bt) * np.exp(-bt * 3.2)
    fade = np.minimum(1, np.minimum(t / 1.0, (dur - t) / 1.5))
    out *= np.clip(fade, 0, 1)
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.5
    st = np.stack([out, out], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- main render
def render(topic, out, use_tts=True, max_seconds=None):
    text = topic["script"]
    tmp = tempfile.mkdtemp()
    voice = os.path.join(tmp, "voice.mp3")
    words = None
    if use_tts:
        words = asyncio.run(_tts(text, voice))
        vdur = duration_of(voice)
        if not words:
            est = estimate_words(text)
            k = vdur / est[-1][1]
            words = [(s * k, e * k, w) for s, e, w in est]
        else:
            words = attach_punct(words, text)
    else:
        words = estimate_words(text)
        vdur = words[-1][1] + 0.2
    words = [(s + VOICE_DELAY, e + VOICE_DELAY, w) for s, e, w in words]
    total = VOICE_DELAY + vdur + TAIL
    if max_seconds:
        total = min(total, max_seconds)
    music = os.path.join(tmp, "music.wav")
    make_music(music, total + 0.5, seed=topic.get("n", 0))

    specs = topic["scenes"]
    n = len(specs)
    bounds = [total * i / n for i in range(n + 1)]
    scenes = [Scene(specs[i], bounds[i + 1] - bounds[i] + XF, seed=1000 + 37 * topic.get("n", 0) + i) for i in range(n)]

    chunks = chunk_words(words)
    chunk_times = [(c[0][0], (chunks[i + 1][0][0] if i + 1 < len(chunks) else c[-1][1] + 0.4)) for i, c in enumerate(chunks)]
    cache = {}
    title = make_title(topic.get("kicker", "DID YOU KNOW?"), topic["label"])
    endcard = render_chunk([(0, 0, "Follow"), (0, 0, "for"), (0, 0, "more!")], 0)
    vign = make_vignette()

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if use_tts:
        cmd += ["-i", voice]
    cmd += ["-i", music]
    if use_tts:
        fc = (f"[1:a]adelay={int(VOICE_DELAY*1000)}|{int(VOICE_DELAY*1000)},apad[v];"
              f"[2:a]volume=0.16[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]")
    else:
        fc = "[1:a]volume=0.16[a]"
    cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-maxrate", "3500k", "-bufsize", "7000k",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nframes = int(total * FPS)
    ci = 0
    for fi in range(nframes):
        T = fi / FPS
        si = min(n - 1, int(T / (total / n)))
        sc = scenes[si]
        fr = sc.frame(T - bounds[si])
        if si + 1 < n and T > bounds[si + 1] - XF:
            a = (T - (bounds[si + 1] - XF)) / XF
            fr = Image.blend(fr, scenes[si + 1].frame(0.0), min(1.0, a))
        fr.paste(vign, (0, 0), vign)
        # title card
        if T < 3.2:
            alpha = min(1.0, T / 0.25) * (1.0 if T < 2.7 else max(0.0, (3.2 - T) / 0.5))
            y = int(230 - 40 * (1 - min(1.0, T / 0.25)))
            ti = title if alpha >= 0.99 else _fade(title, alpha)
            fr.paste(ti, (0, y), ti)
        # subtitles
        while ci + 1 < len(chunks) and T >= chunk_times[ci + 1][0]:
            ci += 1
        cs, ce = chunk_times[ci]
        if cs <= T < ce:
            act = 0
            for k, w in enumerate(chunks[ci]):
                if T >= w[0]:
                    act = k
            key = (ci, act)
            if key not in cache:
                cache[key] = render_chunk(chunks[ci], act)
            im = cache[key]
            age = T - cs
            if age < 0.12:
                s = 0.86 + 0.14 * age / 0.12
                im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
            fr.paste(im, ((W - im.width) // 2, 1240 - im.height // 2), im)
        elif T > words[-1][1] + 0.3:
            fr.paste(endcard, (0, 1240 - endcard.height // 2), endcard)
        proc.stdin.write(fr.tobytes())
        if fi % (FPS * 5) == 0:
            print(f"  frame {fi}/{nframes}", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    return total

def _fade(im, a):
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))

def load_topics():
    with open(os.path.join(HERE, "topics.json"), encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", type=int, default=0)
    ap.add_argument("--out", default="out/video.mp4")
    ap.add_argument("--no-tts", action="store_true")
    ap.add_argument("--seconds", type=float, default=None, help="cut video (for quick tests)")
    ap.add_argument("--still", type=float, default=None, help="save one PNG frame at this second of every scene")
    a = ap.parse_args()
    topics = load_topics()
    tp = topics[a.topic % len(topics)]
    tp["n"] = a.topic % len(topics)
    if a.still is not None:
        for i, sp in enumerate(tp["scenes"]):
            s = Scene(sp, 12, seed=1000 + 37 * tp["n"] + i)
            s.frame(a.still).save(a.out.replace(".png", f"_{i}.png"))
        sys.exit(0)
    dur = render(tp, a.out, use_tts=not a.no_tts, max_seconds=a.seconds)
    print(f"OK {a.out} {dur:.1f}s")
