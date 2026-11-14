#!/usr/bin/env python3
"""
"Why / How" story Shorts (60 s): original cartoon characters on drawn backgrounds,
one-word-at-a-time captions, narrator voice (Edge TTS) + soft music.

  python story_video.py stories/lighthouse.json out/lighthouse.mp4 [--no-tts]
"""
import asyncio, json, math, os, random, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import make_video as mv
from make_video import W, H, FPS, font, mix, ridge, make_music, make_vignette

VOICE = os.environ.get("STORY_VOICE", "en-US-AndrewNeural")
OUT = (34, 26, 40)             # outline colour
SKIN = (255, 212, 168)

# ------------------------------------------------------------------ lighthouses
_LH = {}
def lighthouse(pattern="plain", h=520, lit=False, night=False):
    key = (pattern, h, lit, night)
    if key in _LH:
        return _LH[key]
    w = int(h * 0.26)
    th = int(h * 0.78)
    img = np.zeros((h + 10, w + 40, 4), np.uint8)
    yy, xx = np.mgrid[0:th, 0:w + 40]
    v = yy / th                                   # 0 top .. 1 bottom
    half = (w * 0.30 + (w * 0.5 - w * 0.30) * v)
    cx = (w + 40) / 2
    u = (xx - (cx - half)) / (2 * half)           # 0..1 across tower
    inside = (u >= 0) & (u <= 1)
    A, B = np.array([248, 246, 240]), np.array([30, 30, 36])
    if pattern == "bands":
        m = (np.floor(v * 7) % 2) == 1
    elif pattern == "spiral":
        m = ((u * 1.0 + v * 3.2) % 1.0) < 0.5
    elif pattern == "checker":
        m = ((np.floor(u * 2) + np.floor(v * 8)) % 2) == 1
    elif pattern == "redbands":
        m = (np.floor(v * 5) % 2) == 1
        B = np.array([206, 40, 44])
    elif pattern == "diamond":
        m = ((np.abs(((u * 2) % 1) - 0.5) + np.abs(((v * 4) % 1) - 0.5)) < 0.42)
    else:
        m = np.zeros_like(inside)
    col = np.where(m[..., None], B, A).astype(float)
    col *= (1 - 0.28 * np.clip(u, 0, 1))[..., None]             # shading
    if night:
        col *= 0.28
    tower = np.zeros((th, w + 40, 4), np.uint8)
    tower[..., :3] = col.astype(np.uint8)
    tower[..., 3] = (inside * 255).astype(np.uint8)
    img[h + 10 - th:h + 10] = tower
    im = Image.fromarray(img, "RGBA")
    d = ImageDraw.Draw(im)
    top = h + 10 - th
    gx0, gx1 = cx - w * 0.38, cx + w * 0.38
    dark = (40, 40, 46) if not night else (14, 14, 20)
    d.rectangle([gx0 - 8, top - 10, gx1 + 8, top + 4], fill=dark)                       # gallery
    for k in range(7):
        x = gx0 - 8 + k * (gx1 - gx0 + 16) / 6
        d.line([(x, top - 30), (x, top - 10)], fill=dark, width=3)
    d.line([(gx0 - 8, top - 30), (gx1 + 8, top - 30)], fill=dark, width=3)
    glass = (255, 236, 150) if lit else ((150, 190, 210) if not night else (30, 34, 50))
    d.rectangle([cx - w * 0.26, top - 70, cx + w * 0.26, top - 10], fill=glass, outline=dark, width=4)
    d.pieslice([cx - w * 0.30, top - 110, cx + w * 0.30, top - 40], 180, 360, fill=(40, 40, 46) if not night else (14, 14, 20))
    d.line([(cx, top - 112), (cx, top - 130)], fill=dark, width=4)
    _LH[key] = (im, (int(cx), top - 40))           # image, lamp position
    return _LH[key]

# ------------------------------------------------------------------ characters
def char(d, x, y, s, t, expr="neutral", pose="idle", outfit="sailor", talking=False, look=0.0, seed=0):
    """Original character: chunky body, big round head, huge eyes, outline. (x,y)=feet."""
    bob = math.sin(t * 3.2 + seed) * 4 * s
    y = y + bob
    lw = max(3, int(6 * s))
    body_c = {"sailor": (42, 74, 150), "engineer": (232, 128, 40), "kid": (220, 70, 90)}[outfit]
    # legs
    for dx in (-24, 14):
        d.rounded_rectangle([x + dx * s, y - 46 * s, x + (dx + 22) * s, y], int(8 * s), fill=(60, 54, 70), outline=OUT, width=lw)
        d.ellipse([x + (dx - 6) * s, y - 14 * s, x + (dx + 30) * s, y + 6 * s], fill=(40, 30, 30), outline=OUT, width=lw)
    # arms
    sh_l, sh_r = (x - 52 * s, y - 140 * s), (x + 52 * s, y - 140 * s)
    wave = math.sin(t * 8) * 14 * s
    if pose == "point":
        hands = [(x - 70 * s, y - 70 * s), (x + 150 * s, y - 230 * s + wave * 0.3)]
    elif pose == "shrug":
        hands = [(x - 110 * s, y - 190 * s), (x + 110 * s, y - 190 * s)]
    elif pose == "wave":
        hands = [(x - 70 * s, y - 70 * s), (x + 110 * s, y - 250 * s + wave)]
    elif pose == "hold":
        hands = [(x - 60 * s, y - 120 * s), (x + 60 * s, y - 120 * s)]
    elif pose == "panic":
        hands = [(x - 90 * s, y - 250 * s + wave), (x + 90 * s, y - 250 * s - wave)]
    else:
        hands = [(x - 72 * s, y - 64 * s), (x + 72 * s, y - 64 * s)]
    for sh, hd in zip((sh_l, sh_r), hands):
        d.line([sh, hd], fill=OUT, width=int(26 * s))
        d.line([sh, hd], fill=body_c, width=int(16 * s))
        d.ellipse([hd[0] - 14 * s, hd[1] - 14 * s, hd[0] + 14 * s, hd[1] + 14 * s], fill=SKIN, outline=OUT, width=lw)
    # body
    d.rounded_rectangle([x - 62 * s, y - 170 * s, x + 62 * s, y - 40 * s], int(34 * s), fill=body_c, outline=OUT, width=lw)
    if outfit == "sailor":
        d.polygon([(x - 40 * s, y - 166 * s), (x, y - 120 * s), (x + 40 * s, y - 166 * s)], fill=(250, 250, 250), outline=OUT)
        d.line([(x - 30 * s, y - 160 * s), (x, y - 128 * s), (x + 30 * s, y - 160 * s)], fill=(210, 40, 50), width=max(2, int(5 * s)))
    elif outfit == "engineer":
        d.rectangle([x - 30 * s, y - 130 * s, x + 30 * s, y - 70 * s], fill=(70, 110, 190), outline=OUT, width=max(2, lw // 2))
    # head
    hx, hy, r = x, y - 245 * s, 82 * s
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=SKIN, outline=OUT, width=lw)
    d.ellipse([hx - r * 0.95, hy + r * 0.05, hx - r * 0.65, hy + r * 0.35], fill=(255, 170, 150))   # cheeks
    d.ellipse([hx + r * 0.65, hy + r * 0.05, hx + r * 0.95, hy + r * 0.35], fill=(255, 170, 150))
    # eyes
    blink = (t * 1.0 + seed * 0.37) % 3.3 < 0.12
    big = 1.25 if expr == "shocked" else 1.0
    for ex in (-30, 30):
        cx_, cy_ = hx + ex * s, hy - 14 * s
        ew, eh = 26 * s * big, 32 * s * big
        if blink:
            d.line([(cx_ - ew, cy_), (cx_ + ew, cy_)], fill=OUT, width=lw)
        else:
            d.ellipse([cx_ - ew, cy_ - eh, cx_ + ew, cy_ + eh], fill=(255, 255, 255), outline=OUT, width=lw)
            px = cx_ + look * 10 * s
            pr = 11 * s if expr != "shocked" else 8 * s
            d.ellipse([px - pr, cy_ - pr + 4 * s, px + pr, cy_ + pr + 4 * s], fill=OUT)
            d.ellipse([px - pr * 0.4 + 3 * s, cy_ - pr * 0.4, px + pr * 0.1 + 3 * s, cy_ + pr * 0.1], fill=(255, 255, 255))
    # brows
    by = hy - 56 * s
    if expr == "worried":
        br = [((-52, 6), (-12, -6)), ((12, -6), (52, 6))]
    elif expr == "angry":
        br = [((-52, -8), (-12, 6)), ((12, 6), (52, -8))]
    elif expr == "shocked":
        br = [((-52, -14), (-12, -18)), ((12, -18), (52, -14))]
        by -= 10 * s
    elif expr == "thinking":
        br = [((-52, 0), (-12, 0)), ((12, -10), (52, -4))]
    else:
        br = [((-50, -2), (-14, -8)), ((14, -8), (50, -2))]
    for (a, b) in br:
        d.line([(hx + a[0] * s, by + a[1] * s), (hx + b[0] * s, by + b[1] * s)], fill=OUT, width=int(8 * s))
    # mouth
    my = hy + 36 * s
    open_ = talking and (int(t * 9 + seed) % 2 == 0)
    if expr == "shocked":
        d.ellipse([hx - 16 * s, my - 18 * s, hx + 16 * s, my + 22 * s], fill=(120, 30, 40), outline=OUT, width=lw)
    elif open_:
        d.chord([hx - 26 * s, my - 18 * s, hx + 26 * s, my + 24 * s], 0, 180, fill=(120, 30, 40), outline=OUT, width=lw)
    elif expr in ("happy", "neutral", "thinking"):
        d.arc([hx - 30 * s, my - 26 * s, hx + 30 * s, my + 14 * s], 20, 160, fill=OUT, width=lw)
    else:  # worried / angry
        d.arc([hx - 24 * s, my - 2 * s, hx + 24 * s, my + 26 * s], 200, 340, fill=OUT, width=lw)
    # hats
    if outfit == "sailor":
        d.rounded_rectangle([hx - 70 * s, hy - 112 * s, hx + 70 * s, hy - 66 * s], int(16 * s), fill=(250, 250, 250), outline=OUT, width=lw)
        d.rectangle([hx - 66 * s, hy - 82 * s, hx + 66 * s, hy - 66 * s], fill=(30, 36, 70))
        d.chord([hx - 20 * s, hy - 82 * s, hx + 90 * s, hy - 50 * s], 180, 360, fill=(20, 20, 30))
        d.ellipse([hx - 12 * s, hy - 104 * s, hx + 12 * s, hy - 84 * s], fill=(230, 180, 60), outline=OUT, width=max(2, lw // 2))
    elif outfit == "engineer":
        d.chord([hx - 78 * s, hy - 130 * s, hx + 78 * s, hy - 20 * s], 180, 360, fill=(250, 206, 40), outline=OUT, width=lw)
        d.rectangle([hx - 92 * s, hy - 78 * s, hx + 92 * s, hy - 66 * s], fill=(250, 206, 40), outline=OUT, width=max(2, lw // 2))

def bubble(d, x, y, s, txt, t):
    pop = min(1.0, t / 0.2)
    r = 54 * s * pop
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=OUT, width=6)
    d.polygon([(x - 18 * s, y + r - 6), (x - 40 * s, y + r + 40 * s), (x + 6 * s, y + r - 4)], fill=(255, 255, 255))
    if pop > 0.6:
        d.text((x, y), txt, font=font(int(76 * s)), fill=(220, 50, 60), anchor="mm")

# ------------------------------------------------------------------ backgrounds
def sky_sea(time="day", seed=0, width=W + 260):
    pal = mv.PAL[time]
    yy = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array(pal["top"], float), np.array(pal["bot"], float)
    hz = int(H * 0.55)
    img = top + (bot - top) * np.clip(yy / (hz / H), 0, 1) ** 0.9
    img = np.repeat(img, width, axis=1)
    sea_top = np.array(mv.shade((50, 120, 170), pal, 0.2), float)
    sea_bot = np.array(mv.shade((18, 70, 120), pal, 0.0), float)
    ramp = np.linspace(0, 1, H - hz)[:, None, None]
    img[hz:] = sea_top + (sea_bot - sea_top) * ramp
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    rnd = random.Random(seed)
    if time == "night":
        for _ in range(160):
            x, y, r = rnd.uniform(0, width), rnd.uniform(0, hz - 60), rnd.uniform(1, 3.5)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 240, rnd.randint(120, 255)))
        d.ellipse([width * 0.75 - 60, 260, width * 0.75 + 60, 380], fill=(236, 238, 255))
    else:
        for _ in range(5):
            cx, cy = rnd.uniform(0, width), rnd.uniform(160, hz - 300)
            for k in range(6):
                rr = rnd.uniform(50, 110)
                d.ellipse([cx + k * 60 - rr, cy - rr * 0.7, cx + k * 60 + rr, cy + rr * 0.5], fill=mix((255, 255, 255), pal["bot"], 0.3) + (200,))
    for y in range(hz + 8, H, 22):
        k = (y - hz) / (H - hz)
        for _ in range(int(6 + 10 * k)):
            x = rnd.uniform(0, width)
            d.line([(x, y), (x + 20 + 70 * k, y)], fill=(230, 245, 255, int(40 + 60 * k)), width=max(2, int(4 * k)))
    return im, hz

def coast(d, width, hz, time, seed=1, color=(86, 120, 80)):
    pal = mv.PAL[time]
    xs, ys = ridge(width, hz - 30, 70, seed)
    d.polygon(list(zip(xs, ys)) + [(width, hz + 6), (0, hz + 6)], fill=mv.shade(color, pal, 0.35))
    return mv.ridge_fn(xs, ys)

def paste_lh(im, x, base, pattern, h, lit=False, night=False):
    lh, lamp = lighthouse(pattern, h, lit, night)
    im.paste(lh, (int(x - lh.width / 2), int(base - lh.height)), lh)
    return (x - lh.width / 2 + lamp[0], base - lh.height + lamp[1])

def deck(d, width, time):
    pal = mv.PAL[time]
    wood, dark = mv.shade((150, 98, 58), pal, 0), mv.shade((104, 66, 38), pal, 0)
    d.polygon([(0, H * 0.80), (width, H * 0.78), (width, H), (0, H)], fill=wood)
    for k in range(8):
        y = H * 0.81 + k * 50
        d.line([(0, y), (width, y - 8)], fill=dark, width=4)
    d.rectangle([0, H * 0.72, width, H * 0.74], fill=dark)               # rail
    for x in range(0, width, 90):
        d.rectangle([x, H * 0.72, x + 16, H * 0.80], fill=dark)

def wheel(d, x, y, t, time):
    pal = mv.PAL[time]
    c = mv.shade((120, 76, 40), pal, 0)
    rot = math.sin(t * 1.4) * 0.3
    for k in range(8):
        a = rot + k * math.pi / 4
        d.line([(x, y), (x + 150 * math.cos(a), y + 150 * math.sin(a))], fill=c, width=14)
        d.ellipse([x + 150 * math.cos(a) - 14, y + 150 * math.sin(a) - 14, x + 150 * math.cos(a) + 14, y + 150 * math.sin(a) + 14], fill=c)
    d.ellipse([x - 110, y - 110, x + 110, y + 110], outline=c, width=22)
    d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=c)

def rocks(d, width, hz, time, seed=3):
    pal = mv.PAL[time]
    rnd = random.Random(seed)
    for i in range(7):
        x = rnd.uniform(0, width)
        y = hz + rnd.uniform(150, 600)
        s = rnd.uniform(90, 220)
        pts = [(x - s, y), (x - s * 0.6, y - s * 0.9), (x - s * 0.1, y - s * 1.3), (x + s * 0.5, y - s * 0.8), (x + s, y)]
        d.polygon(pts, fill=mv.shade((70, 70, 78), pal, 0))
        d.polygon([pts[2], pts[3], pts[4], (x + s * 0.2, y)], fill=mv.shade((48, 48, 56), pal, 0))
        d.ellipse([x - s * 1.2, y - 20, x + s * 1.2, y + 30], fill=(240, 248, 255, 180))

def workshop():
    im = Image.new("RGB", (W + 260, H), (196, 168, 132))
    d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, W + 260, 120):
        d.line([(x, 0), (x, H * 0.7)], fill=(176, 148, 112), width=6)
    d.rectangle([0, H * 0.70, W + 260, H], fill=(120, 86, 60))
    d.rectangle([700, 360, 1080, 760], fill=(150, 200, 230), outline=(90, 60, 40), width=20)
    d.line([(890, 360), (890, 760)], fill=(90, 60, 40), width=14)
    d.line([(700, 560), (1080, 560)], fill=(90, 60, 40), width=14)
    for i, (c, x) in enumerate([((30, 30, 36), 120), ((206, 40, 44), 260), ((248, 246, 240), 400)]):
        y = H * 0.70 + 60
        d.rectangle([x, y - 110, x + 110, y], fill=(170, 170, 176), outline=OUT, width=6)
        d.ellipse([x, y - 126, x + 110, y - 94], fill=c, outline=OUT, width=6)
        d.line([(x + 90, y - 110), (x + 120, y - 150 - i * 10)], fill=(140, 90, 50), width=10)
    # blueprint on wall
    d.rectangle([180, 380, 560, 760], fill=(40, 90, 170), outline=(250, 250, 250), width=6)
    for k, pat in enumerate(["plain", "bands", "spiral"]):
        lh, _ = lighthouse(pat, 260)
        im.paste(lh.resize((lh.width // 2 + 10, 300)), (210 + k * 120, 420), lh.resize((lh.width // 2 + 10, 300)))
    return im

def chart_bg():
    im = Image.new("RGB", (W + 260, H), (120, 80, 50))
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([60, 260, W + 200, 1500], 30, fill=(238, 222, 184), outline=(150, 120, 80), width=10)
    pts = [(160 + k * 46, 520 + 90 * math.sin(k * 0.7) + k * 30) for k in range(21)]
    d.line(pts, fill=(80, 120, 160), width=10)
    d.polygon(pts + [(W + 200, 1500), (60, 1500), (60, 520)], fill=(214, 230, 200, 120))
    for k, (pat, lbl) in enumerate([("bands", "Bodie"), ("spiral", "Hatteras"), ("diamond", "Lookout")]):
        x, y = 300 + k * 330, 640 + k * 70
        lh, _ = lighthouse(pat, 360)
        im.paste(lh, (int(x - lh.width / 2), int(y - lh.height + 340)), lh)
        d.text((x, y + 380), lbl, font=font(44), fill=(60, 40, 30), anchor="mm")
    d.ellipse([480, 870, 820, 1160], outline=(210, 40, 50), width=12)
    return im

# ------------------------------------------------------------------ scenes
class StoryScene:
    def __init__(self, sp, dur, seed):
        self.sp, self.dur, self.seed = sp, dur, seed
        bg = sp.get("bg", "scene")
        time = sp.get("time", "day")
        self.time = time
        self.lamps = []
        self.mv_scene = None
        if bg == "scene":
            self.mv_scene = mv.Scene(sp, dur, seed)
            self.base = None
            self.zoom_in = True
            return
        if bg == "workshop":
            self.base = workshop()
        elif bg == "chart":
            self.base = chart_bg()
        else:
            im, hz = sky_sea(time, seed)
            d = ImageDraw.Draw(im, "RGBA")
            night = time == "night"
            if bg in ("coast_one", "coast_same", "coast_patterns", "night_row", "spiral_hero"):
                coast(d, im.width, hz, time, seed)
            if bg == "coast_one":
                self.lamps.append(paste_lh(im, im.width * 0.62, hz - 10, "plain", 300, lit=True, night=night))
            elif bg == "coast_same":
                for i in range(5):
                    paste_lh(im, 140 + i * 230, hz - 10 + (i % 2) * 8, "plain", 330 - (i % 2) * 40, night=night)
            elif bg == "coast_patterns":
                for i, p in enumerate(["bands", "spiral", "checker", "redbands", "diamond"]):
                    paste_lh(im, 160 + i * 220, hz - 10 + (i % 2) * 10, p, 420 - (i % 2) * 50)
            elif bg == "spiral_hero":
                paste_lh(im, im.width * 0.55, hz + 40, "spiral", 1000)
            elif bg == "night_row":
                for i in range(3):
                    self.lamps.append(paste_lh(im, 260 + i * 360, hz - 10, ["bands", "spiral", "checker"][i], 520, lit=True, night=True))
            if bg in ("coast_same", "coast_patterns", "night_row", "spiral_hero"):
                pal = mv.PAL[time]
                xs, ys = ridge(im.width, int(H * 0.87), 40, seed + 7)
                d.polygon(list(zip(xs, ys)) + [(im.width, H), (0, H)], fill=mv.shade((226, 196, 140), pal, 0))
                xs2 = [x for x in xs]
                d.line(list(zip(xs2, [y - 4 for y in ys])), fill=(250, 252, 255, 160), width=10)
                rnd = random.Random(seed)
                for _ in range(40):
                    x, y = rnd.uniform(0, im.width), rnd.uniform(H * 0.9, H)
                    d.ellipse([x - 6, y - 3, x + 6, y + 3], fill=mv.shade((190, 160, 110), pal, 0))
            if bg == "rocks":
                rocks(d, im.width, hz, time, seed)
            if bg == "deck":
                self.lamps_far = paste_lh(im, im.width * 0.72, hz, "plain", 160, lit=True, night=night) if sp.get("far_lh") else None
                deck(d, im.width, time)
            self.base = im
        self.zoom_in = random.Random(seed).random() < 0.6

    def _draw_chars(self, d, t, talking):
        sp = self.sp
        # characters
        for c in sp.get("chars", []):
            if c.get("outfit") == "bolt":
                import mascot
                mascot.robot(d, c.get("x", 0.35) * W, c.get("y", 0.86) * H, c.get("s", 1.0), t, c.get("expr", "neutral"),
                             c.get("pose", "idle"), talking and c.get("talk", True))
                continue
            cx = c.get("x", 0.35) * W
            cy = c.get("y", 0.86) * H
            char(d, cx, cy, c.get("s", 1.15), t, c.get("expr", "neutral"), c.get("pose", "idle"),
                 c.get("outfit", "sailor"), talking and c.get("talk", False), c.get("look", 0), seed=self.seed)
        if sp.get("bubble"):
            c0 = sp["chars"][0]
            bubble(d, c0.get("x", 0.35) * W + 150, c0.get("y", 0.86) * H - 500 * c0.get("s", 1.15), 1.2, sp["bubble"], t)

    def frame(self, t, talking):
        sp = self.sp
        if self.mv_scene is not None:
            f = self.mv_scene.frame(t)
            d = ImageDraw.Draw(f, "RGBA")
            self._draw_chars(d, t, talking)
            return f
        pan = 200 * t / max(self.dur, 0.1)
        f = self.base.crop((int(pan), 0, int(pan) + W, H))
        d = ImageDraw.Draw(f, "RGBA")
        bg = sp["bg"]
        # flashing lights
        for i, (lx, ly) in enumerate(self.lamps):
            lx -= pan
            if bg == "night_row":
                on = [(t % 2.4) < 0.5, (t % 3.0) < 0.3 or 0.6 < (t % 3.0) < 0.9, (t % 4.0) < 2.0][i]
            else:
                on = True
            if on:
                for rr, a in [(170, 40), (90, 90), (40, 200)]:
                    d.ellipse([lx - rr, ly - rr, lx + rr, ly + rr], fill=(255, 236, 160, a))
                if bg != "night_row" or i == 2:
                    ang = t * 1.6 + i
                    p1 = (lx + 900 * math.cos(ang - 0.07), ly + 200 * math.sin(ang - 0.07))
                    p2 = (lx + 900 * math.cos(ang + 0.07), ly + 200 * math.sin(ang + 0.07))
                    d.polygon([(lx, ly), p1, p2], fill=(255, 240, 180, 50))
        if bg == "deck":
            wheel(d, W * 0.66, H * 0.70, t, self.time)
        if bg == "rocks":
            for c in sp.get("chars", []):
                bx, byy = c.get("x", 0.35) * W, c.get("y", 0.86) * H + math.sin(t * 2) * 8
                d.polygon([(bx - 230, byy - 60), (bx + 230, byy - 60), (bx + 170, byy + 50), (bx - 170, byy + 50)], fill=(140, 86, 48), outline=OUT)
                d.line([(bx - 230, byy - 60), (bx + 230, byy - 60)], fill=(100, 60, 34), width=14)
        self._draw_chars(d, t, talking)
        p = t / max(self.dur, 0.1)
        z = 1.04 + 0.07 * (p if self.zoom_in else 1 - p)
        z += 0.10 * math.exp(-t * 7)                                   # punch-in at the cut
        cw, ch = W / z, H / z
        sx = sy = 0.0
        if sp.get("shake"):
            amp = 14 * (0.4 + 0.6 * abs(math.sin(t * 1.3)))
            sx, sy = amp * math.sin(t * 37), amp * math.cos(t * 29)
        x0 = (W - cw) / 2 + sx
        y0 = (H - ch) * 0.55 + sy
        x0 = min(max(0, x0), W - cw); y0 = min(max(0, y0), H - ch)
        return f.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))

# ------------------------------------------------------------------ captions (one word at a time)
_WCACHE = {}
EMPH = set()
def word_img(w):
    key = w.lower().strip(".,!?;:'\"")
    hot = key in EMPH or any(ch.isdigit() for ch in key)
    if (w, hot) not in _WCACHE:
        f = font(128 if hot else 118)
        tw = int(f.getlength(w)) + 60
        im = Image.new("RGBA", (tw, 200), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((tw / 2, 100), w, font=f, fill=(255, 214, 64) if hot else (255, 255, 255),
                                anchor="mm", stroke_width=12, stroke_fill=(10, 10, 16))
        _WCACHE[(w, hot)] = im
    return _WCACHE[(w, hot)]


def _pcm(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32), sr

def align_line(path, line, t0, dur):
    """Split the line into phrases at punctuation, match them to the longest pauses in the audio,
    then spread words inside each phrase by length. Returns [(start, end, word)]."""
    toks = line.split()
    phrases, cur = [], []
    for w in toks:
        cur.append(w)
        if w[-1] in ".,!?;:":
            phrases.append(cur); cur = []
    if cur:
        phrases.append(cur)
    x, sr = _pcm(path)
    hop = int(sr * 0.01)
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, max(1, len(x) - hop), hop)]) + 1e-6
    thr = max(env.max() * 0.06, np.percentile(env, 20) * 1.5)
    quiet = env < thr
    pauses, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if j - i >= 6 and i > 5 and j < len(quiet) - 5:
                pauses.append((j - i, (i + j) / 2 * 0.01))
            i = j
        else:
            i += 1
    need = len(phrases) - 1
    cuts = sorted(c for _, c in sorted(pauses, reverse=True)[:need])
    if len(cuts) < need:                              # not enough pauses: proportional fallback
        lens = [sum(len(w) + 1 for w in p) for p in phrases]
        acc, cuts = 0, []
        for L in lens[:-1]:
            acc += L
            cuts.append(dur * acc / sum(lens))
    bounds = [0.0] + cuts + [dur]
    out = []
    for p, (a, b) in zip(phrases, zip(bounds, bounds[1:])):
        wts = [0.8 + len(w.strip(".,!?;:")) for w in p]
        tot, acc = sum(wts), 0.0
        span = (b - a) * 0.96
        for w, wt in zip(p, wts):
            s0 = a + span * acc / tot
            acc += wt
            out.append((t0 + s0, t0 + a + span * acc / tot, w))
    return out

def make_fx(path, total, starts, story):
    """Sound effects: whoosh on every cut, sea ambience on sea scenes, ding on emphasis scenes."""
    sr = 44100
    n = int(sr * (total + 0.5))
    out = np.zeros(n, np.float32)
    rnd = np.random.default_rng(3)
    for k, st in enumerate(starts[1:], 1):            # whoosh
        L = int(sr * 0.45)
        noise = rnd.standard_normal(L).astype(np.float32)
        env = np.sin(np.linspace(0, np.pi, L)) ** 2
        # crude band sweep: mix of smoothed noise with rising cutoff
        sm = np.convolve(noise, np.ones(24) / 24, mode="same")
        sweep = sm + (noise - sm) * np.linspace(0, 1, L)
        i0 = max(0, int(sr * (st - 0.25)))
        seg = (sweep * env * 0.18)[:n - i0]
        out[i0:i0 + len(seg)] += seg
    ends = starts[1:] + [total]
    for sc, a, b in zip(story["scenes"], starts, ends):
        bg = sc["bg"]
        if bg in ("deck", "rocks", "coast_one", "coast_same", "coast_patterns", "night_row", "spiral_hero"):
            i0, i1 = int(sr * a), min(n, int(sr * b))
            L = i1 - i0
            br = np.cumsum(rnd.standard_normal(L)).astype(np.float32)
            br -= np.convolve(br, np.ones(2000) / 2000, mode="same")
            br /= (np.abs(br).max() + 1e-6)
            tt = np.arange(L) / sr
            swell = 0.55 + 0.45 * np.sin(2 * np.pi * tt / 5.5)
            fade = np.minimum(1, np.minimum(tt / 0.3, (L / sr - tt) / 0.3))
            out[i0:i1] += br * swell * fade * (0.10 if bg != "rocks" else 0.16)
        if sc.get("ding"):
            i0 = int(sr * (a + sc.get("ding_at", 0.3)))
            L = min(n - i0, int(sr * 1.6))
            tt = np.arange(L) / sr
            tone = (np.sin(2 * np.pi * 1318 * tt) + 0.5 * np.sin(2 * np.pi * 1976 * tt)) * np.exp(-tt * 4)
            out[i0:i0 + L] += tone * 0.12
    out = np.clip(out, -1, 1)
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((out * 32767).astype(np.int16).tobytes())

# ------------------------------------------------------------------ render
def render(story, out, use_tts=True):
    lines = [sc["text"] for sc in story["scenes"]]
    full = " ".join(lines)
    EMPH.clear(); EMPH.update(w.lower().strip(".,!?;:'\"") for w in story.get("emph", []))
    tmp = tempfile.mkdtemp()
    voice = os.path.join(tmp, "v.mp3")
    if isinstance(use_tts, str):                      # folder with line_XX.aiff per scene (Mac "say")
        GAP = 0.12
        TEMPO = float(os.environ.get("VOICE_TEMPO", "1.07"))
        chain = (f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                 f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                 f"highpass=f=70,equalizer=f=180:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1.5:g=2.5,"
                 f"acompressor=threshold=-20dB:ratio=3:attack=5:release=80,atempo={TEMPO},"
                 f"aresample=44100")
        parts, words, t = [], [], 0.0
        for i, line in enumerate(lines, 1):
            src = os.path.join(use_tts, f"line_{i:02d}.aiff")
            f = os.path.join(tmp, f"p{i:02d}.wav")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", chain, "-ac", "1", f], check=True)
            dd = mv.duration_of(f)
            words += align_line(f, line, t, dd)
            parts.append(f)
            t += dd + GAP
        lst = os.path.join(tmp, "l.txt")
        sil = os.path.join(tmp, "sil.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", str(GAP), sil], check=True)
        with open(lst, "w") as fh:
            for f in parts:
                fh.write(f"file '{os.path.abspath(f)}'\nfile '{sil}'\n")
        raw = os.path.join(tmp, "raw.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, raw], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "44100", voice], check=True)
        vdur = mv.duration_of(voice)
        use_tts = True
    elif use_tts:
        mv.VOICE = VOICE
        mv.RATE = "+4%"
        words = mv.attach_punct(asyncio.run(mv._tts(full, voice)), full)
        vdur = mv.duration_of(voice)
    else:
        words = []
        t = 0.0
        for w in full.split():
            dd = 0.13 + 0.045 * len(w)
            words.append((t, t + dd, w))
            t += dd + (0.30 if w[-1] in ".!?" else 0.12 if w[-1] in ",;:" else 0.01)
        vdur = t
    D0 = 0.15
    words = [(s + D0, e + D0, w) for s, e, w in words]
    total = D0 + vdur + 0.8
    # scene boundaries = first word of each scene line
    counts = [len(l.split()) for l in lines]
    starts, k = [], 0
    for c in counts:
        starts.append(words[min(k, len(words) - 1)][0] if k else 0.0)
        k += c
    ends = starts[1:] + [total]
    scenes = [StoryScene(sp, ends[i] - starts[i], 500 + i) for i, sp in enumerate(story["scenes"])]
    music = os.path.join(tmp, "m.wav")
    make_music(music, total + 0.5, seed=story.get("music", 1))
    vign = make_vignette()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if use_tts:
        fx = os.path.join(tmp, "fx.wav")
        make_fx(fx, total, starts, story)
        cmd += ["-i", voice, "-i", music, "-i", fx, "-filter_complex",
                f"[1:a]adelay={int(D0*1000)}|{int(D0*1000)},apad[v];[2:a]volume=0.09[m];[3:a]volume=1.0[f];"
                f"[v][m][f]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[a]"]
    else:
        cmd += ["-i", music, "-filter_complex", "[1:a]volume=0.20[a]"]
    cmd += ["-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-maxrate", "4000k", "-bufsize", "8000k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    wi = 0
    for fi in range(int(total * FPS)):
        T = fi / FPS
        si = max(i for i in range(len(starts)) if starts[i] <= T)
        while wi + 1 < len(words) and words[wi + 1][0] <= T:
            wi += 1
        talking = words[0][0] <= T <= words[-1][1] and (words[wi][0] <= T <= words[wi][1] + 0.08)
        fr = scenes[si].frame(T - starts[si], talking)
        if T < starts[si] + 0.12 and si > 0:                      # quick flash cut
            fr = Image.blend(fr, scenes[si - 1].frame(T - starts[si - 1], talking), 1 - (T - starts[si]) / 0.12)
        fr.paste(vign, (0, 0), vign)
        if words[0][0] <= T <= words[-1][1] + 0.3:
            w = words[wi][2]
            im = word_img(w)
            age = T - words[wi][0]
            if age < 0.08:
                sc = 0.8 + 0.2 * age / 0.08
                im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
            fr.paste(im, ((W - im.width) // 2, int(H * 0.47) - im.height // 2), im)
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError("ffmpeg failed")
    return total

def make_mac_voice(story, outdir, voice="Daniel", rate=180):
    """macOS only: one AIFF per scene line with the built-in 'say' voice (channel voice = Daniel)."""
    os.makedirs(outdir, exist_ok=True)
    for i, sc in enumerate(story["scenes"], 1):
        txt = sc.get("say", sc["text"]).replace("1800s", "eighteen hundreds")
        tf = os.path.join(outdir, f"line_{i:02d}.txt")
        with open(tf, "w") as fh:
            fh.write(txt + "\n")
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", os.path.join(outdir, f"line_{i:02d}.aiff"), "-f", tf], check=True)
    return outdir


if __name__ == "__main__":
    story = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    mode = True
    if "--no-tts" in sys.argv:
        mode = False
    if "--voice-dir" in sys.argv:
        mode = sys.argv[sys.argv.index("--voice-dir") + 1]
    if "--mac-voice" in sys.argv:
        mode = make_mac_voice(story, tempfile.mkdtemp())
    print("OK", render(story, out, use_tts=mode))
