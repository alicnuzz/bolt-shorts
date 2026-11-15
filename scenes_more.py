"""More modern scenes: AI chat, next-word prediction, drag strip, torque gauges, undersea cables."""
import math, random
import make_video as mv
from tech_scenes import _car, _skyline

def _txt(d, x, y, s, size, fill=(255, 255, 255), anchor="mm"):
    d.text((x, y), s, font=mv.font(size), fill=fill, anchor=anchor)

def _bubble(d, x0, y0, x1, y1, col, lines=3, tail="l"):
    d.rounded_rectangle([x0, y0, x1, y1], 36, fill=col)
    tx = x0 + 40 if tail == "l" else x1 - 40
    d.polygon([(tx - 26, y1 - 6), (tx + 26, y1 - 6), (tx + (-34 if tail == "l" else 34), y1 + 36)], fill=col)
    for i in range(lines):
        w = (x1 - x0 - 80) * (1.0 if i < lines - 1 else 0.6)
        d.rounded_rectangle([x0 + 40, y0 + 34 + i * 40, x0 + 40 + w, y0 + 52 + i * 40], 9, fill=mv.dk(col, 0.78))

def lm_chat(img, d, cx, by, sc, ctx, mark=None):
    x0, y0, x1, y1 = cx - 330, by - 800, cx + 330, by - 40
    d.rounded_rectangle([x0, y0, x1, y1], 56, fill=sc((30, 36, 54)))
    d.rounded_rectangle([x0 + 20, y0 + 20, x1 - 20, y1 - 20], 42, fill=sc((236, 240, 248)))
    _bubble(d, x0 + 250, y0 + 70, x1 - 50, y0 + 220, sc((150, 160, 184)), 2, "r")
    _bubble(d, x0 + 50, y0 + 290, x1 - 150, y0 + 500, sc((40, 190, 170)), 4, "l")
    if mark == "bad":
        c = sc((240, 70, 70))
        d.ellipse([cx + 60, y0 + 520, cx + 260, y0 + 720], fill=c)
        d.line([(cx + 110, y0 + 570), (cx + 210, y0 + 670)], fill=(255, 255, 255), width=26)
        d.line([(cx + 210, y0 + 570), (cx + 110, y0 + 670)], fill=(255, 255, 255), width=26)
    elif mark == "ok":
        c = sc((60, 200, 120))
        d.ellipse([cx + 60, y0 + 520, cx + 260, y0 + 720], fill=c)
        d.line([(cx + 104, y0 + 624), (cx + 146, y0 + 668), (cx + 220, y0 + 578)], fill=(255, 255, 255), width=26, joint="curve")
    else:
        _txt(d, cx - 130, y0 + 620, "?", 170, sc((120, 130, 160)))

def lm_nextword(img, d, cx, by, sc, ctx):
    y = by - 760
    words, x = ["The", "sky", "is"], cx - 330
    for w in words:
        ww = d.textlength(w, font=mv.font(74)) + 56
        d.rounded_rectangle([x, y, x + ww, y + 120], 26, fill=sc((236, 240, 248)))
        _txt(d, x + ww / 2, y + 58, w, 74, (30, 36, 54))
        x += ww + 18
    d.rounded_rectangle([x, y, x + 150, y + 120], 26, outline=sc((255, 206, 84)), width=10)
    _txt(d, x + 75, y + 56, "?", 80, sc((255, 206, 84)))
    opts = [("blue", 0.92, (80, 170, 255)), ("clear", 0.06, (92, 230, 150)), ("soup", 0.02, (255, 128, 110))]
    for i, (w, p, col) in enumerate(opts):
        yy = y + 210 + i * 150
        d.rounded_rectangle([cx - 330, yy, cx + 330, yy + 110], 26, fill=sc((40, 46, 66)))
        d.rounded_rectangle([cx - 330, yy, cx - 330 + max(60, 660 * p), yy + 110], 26, fill=sc(col))
        _txt(d, cx - 300, yy + 52, w, 60, (255, 255, 255), "lm")
        _txt(d, cx + 310, yy + 52, f"{int(p * 100)}%", 60, (255, 255, 255), "rm")

def lm_dragstrip(img, d, cx, by, sc, ctx):
    _skyline(d, cx, by - 30, sc, seed=21, hmax=360)
    d.rectangle([cx - 700, by - 30, cx + 700, by + 60], fill=sc((48, 52, 66)))
    for x in range(int(cx - 700), int(cx + 700), 120):
        d.rectangle([x, by + 8, x + 60, by + 18], fill=sc((236, 236, 236)))
    _car(d, cx + 140, by - 30, sc, col=(40, 190, 170), s=0.62)
    _car(d, cx - 190, by + 56, sc, col=(226, 76, 70), s=0.62)
    px = cx - 420
    d.rectangle([px - 10, by - 430, px + 10, by - 30], fill=sc((70, 76, 96)))
    d.rounded_rectangle([px - 50, by - 560, px + 50, by - 400], 20, fill=sc((30, 34, 46)))
    d.ellipse([px - 30, by - 546, px + 30, by - 486], fill=sc((90, 40, 40)))
    d.ellipse([px - 30, by - 474, px + 30, by - 414], fill=sc((92, 240, 140)))

def lm_gauge(img, d, cx, by, sc, ctx, level=1.0, label="TORQUE", col=(92, 230, 150)):
    r, cy = 330, by - 330
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=sc((36, 42, 62)))
    d.pieslice([cx - r + 30, cy - r + 30, cx + r - 30, cy + r - 30], 180, 180 + 180 * level, fill=sc(col))
    d.pieslice([cx - r + 110, cy - r + 110, cx + r - 110, cy + r - 110], 180, 360, fill=sc((36, 42, 62)))
    a = math.radians(180 + 180 * level)
    d.line([(cx, cy), (cx + (r - 60) * math.cos(a), cy + (r - 60) * math.sin(a))], fill=(255, 255, 255), width=18)
    d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(255, 255, 255))
    d.rounded_rectangle([cx - r, cy, cx + r, cy + 130], 30, fill=sc((36, 42, 62)))
    _txt(d, cx, cy + 62, label, 76)
    _txt(d, cx - r + 70, cy - 40, "0", 54, sc((170, 180, 200)))
    _txt(d, cx + r - 80, cy - 40, "MAX", 46, sc((170, 180, 200)))

def lm_cableship(img, d, cx, by, sc, ctx):
    hull, deck = sc((44, 60, 96)), sc((236, 240, 246))
    y = mv.HORIZON + 6
    d.polygon([(cx - 330, y - 110), (cx + 330, y - 110), (cx + 260, y), (cx - 280, y)], fill=hull)
    d.rectangle([cx - 330, y - 124, cx + 330, y - 104], fill=sc((226, 76, 70)))
    d.rectangle([cx - 120, y - 250, cx + 90, y - 124], fill=deck)
    d.rectangle([cx - 80, y - 320, cx + 20, y - 250], fill=deck)
    for wx in (-90, -30, 30):
        d.rectangle([cx + wx, y - 220, cx + wx + 36, y - 180], fill=sc((120, 190, 240)))
    d.ellipse([cx + 150, y - 230, cx + 290, y - 90], fill=sc((255, 180, 60)))      # cable drum
    d.ellipse([cx + 190, y - 190, cx + 250, y - 130], fill=sc((180, 110, 30)))
    pts = [(cx + 300, y - 150)]
    for i in range(1, 31):
        t = i / 30
        pts.append((cx + 300 + 120 * t + 30 * math.sin(t * 6), y - 150 + (mv.H - y + 150) * t ** 1.3))
    d.line(pts, fill=(20, 22, 30), width=14, joint="curve")

def lm_cablecut(img, d, cx, by, sc, ctx):
    cy = by - 420
    rings = [(340, (30, 32, 40)), (290, (150, 156, 170)), (230, (40, 44, 56)), (180, (214, 132, 70)), (120, (236, 240, 246))]
    for r, col in rings:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sc(col))
    for k in range(18):                                   # steel wires
        a = k / 18 * 6.283
        x, y = cx + 260 * math.cos(a), cy + 260 * math.sin(a)
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=sc((200, 206, 220)))
    rnd = random.Random(4)
    for k in range(8):                                    # glass fibres
        a = k / 8 * 6.283
        x, y = cx + 62 * math.cos(a), cy + 62 * math.sin(a)
        d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=sc(rnd.choice([(80, 200, 255), (255, 206, 84), (92, 230, 150), (255, 128, 110)])))
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=sc((80, 200, 255)))

def lm_globe(img, d, cx, by, sc, ctx):
    r, cy = 340, by - 420
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sc((40, 120, 200)))
    land = sc((92, 190, 120))
    for (dx, dy, w, h) in [(-210, -150, 200, 170), (-170, 30, 130, 200), (40, -190, 220, 150), (60, -20, 150, 220), (190, 90, 110, 90)]:
        d.ellipse([cx + dx, cy + dy, cx + dx + w, cy + dy + h], fill=land)
    glow = sc((255, 226, 120))
    nodes = [(-130, -70), (-110, 120), (130, -110), (130, 90), (240, 130), (10, 250)]
    for (a, b) in [(0, 2), (0, 1), (2, 3), (1, 3), (3, 4), (1, 5), (0, 3)]:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + 50
        pts = [((1 - t) ** 2 * x1 + 2 * (1 - t) * t * mx + t * t * x2 + cx, (1 - t) ** 2 * y1 + 2 * (1 - t) * t * my + t * t * y2 + cy)
               for t in [i / 16 for i in range(17)]]
        d.line(pts, fill=glow, width=8, joint="curve")
    for (x, y) in nodes:
        d.ellipse([cx + x - 16, cy + y - 16, cx + x + 16, cy + y + 16], fill=(255, 255, 255))

mv.LANDMARKS.update({
    "chat": lm_chat, "chat_bad": lambda *a: lm_chat(*a, mark="bad"), "chat_ok": lambda *a: lm_chat(*a, mark="ok"),
    "nextword": lm_nextword, "dragstrip": lm_dragstrip,
    "torque_full": lambda *a: lm_gauge(*a, level=1.0), "torque_low": lambda *a: lm_gauge(*a, level=0.22, col=(255, 128, 110)),
    "cableship": lm_cableship, "cablecut": lm_cablecut, "globe": lm_globe,
})
