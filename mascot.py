"""Channel mascot candidates — original designs, drawn with code.
draw(style, d, x, y, s, t, expr, pose, talking)   (x, y) = feet position
"""
import math
from PIL import Image, ImageDraw
from make_video import font

OUT = (30, 24, 36)
SKIN = (255, 206, 160)

def _eyes(d, hx, hy, s, t, expr, gap=30, size=1.0, seed=0):
    blink = (t + seed * 0.37) % 3.4 < 0.12
    for ex in (-gap, gap):
        cx, cy = hx + ex * s, hy
        ew, eh = 20 * s * size, 26 * s * size
        if expr == "shocked":
            ew, eh = ew * 1.25, eh * 1.25
        if blink:
            d.line([(cx - ew, cy), (cx + ew, cy)], fill=OUT, width=int(6 * s))
            continue
        if expr == "happy":
            d.arc([cx - ew, cy - eh * 0.6, cx + ew, cy + eh * 0.9], 200, 340, fill=OUT, width=int(8 * s))
            continue
        d.ellipse([cx - ew, cy - eh, cx + ew, cy + eh], fill=(255, 255, 255), outline=OUT, width=int(5 * s))
        pr = 9 * s * size
        d.ellipse([cx - pr, cy - pr + 3 * s, cx + pr, cy + pr + 3 * s], fill=OUT)
        d.ellipse([cx - pr * 0.3 + 3 * s, cy - pr * 0.5, cx + pr * 0.2 + 3 * s, cy], fill=(255, 255, 255))

def _brows(d, hx, by, s, expr, gap=30, col=OUT, w=9):
    shapes = {"worried": [(-48, 8, -12, -4), (12, -4, 48, 8)],
              "angry": [(-48, -8, -12, 6), (12, 6, 48, -8)],
              "shocked": [(-48, -16, -12, -20), (12, -20, 48, -16)],
              "thinking": [(-48, 0, -12, 0), (12, -12, 48, -4)]}
    for x0, y0, x1, y1 in shapes.get(expr, [(-46, -2, -14, -8), (14, -8, 46, -2)]):
        d.line([(hx + x0 * s * gap / 30, by + y0 * s), (hx + x1 * s * gap / 30, by + y1 * s)], fill=col, width=int(w * s))

def _arms(d, x, y, s, t, pose, col, sh_y=150, hand=SKIN):
    sh_l, sh_r = (x - 58 * s, y - sh_y * s), (x + 58 * s, y - sh_y * s)
    wave = math.sin(t * 8) * 14 * s
    hands = {"point": [(x - 76 * s, y - 70 * s), (x + 165 * s, y - (sh_y + 90) * s)],
             "shrug": [(x - 120 * s, y - (sh_y + 40) * s), (x + 120 * s, y - (sh_y + 40) * s)],
             "wave": [(x - 76 * s, y - 70 * s), (x + 120 * s, y - (sh_y + 110) * s + wave)],
             "panic": [(x - 95 * s, y - (sh_y + 110) * s + wave), (x + 95 * s, y - (sh_y + 110) * s - wave)],
             "think": [(x - 76 * s, y - 70 * s), (x + 20 * s, y - (sh_y + 70) * s)]}.get(
        pose, [(x - 80 * s, y - 64 * s), (x + 80 * s, y - 64 * s)])
    for sh, hd in zip((sh_l, sh_r), hands):
        d.line([sh, hd], fill=OUT, width=int(30 * s))
        d.line([sh, hd], fill=col, width=int(19 * s))
        d.ellipse([hd[0] - 16 * s, hd[1] - 16 * s, hd[0] + 16 * s, hd[1] + 16 * s], fill=hand, outline=OUT, width=int(5 * s))

def _mouth(d, hx, my, s, t, expr, talking, w=1.0):
    lw = int(6 * s)
    if expr == "shocked":
        d.ellipse([hx - 16 * s, my - 16 * s, hx + 16 * s, my + 22 * s], fill=(110, 30, 40), outline=OUT, width=lw)
    elif talking and int(t * 9) % 2 == 0:
        d.chord([hx - 26 * s * w, my - 16 * s, hx + 26 * s * w, my + 26 * s], 0, 180, fill=(110, 30, 40), outline=OUT, width=lw)
    elif expr in ("worried", "angry"):
        d.arc([hx - 22 * s, my, hx + 22 * s, my + 24 * s], 200, 340, fill=OUT, width=lw)
    else:
        d.arc([hx - 30 * s * w, my - 24 * s, hx + 30 * s * w, my + 16 * s], 20, 160, fill=OUT, width=lw)

# ---------------------------------------------------------------- A: Captain Finn
def captain(d, x, y, s, t, expr="neutral", pose="idle", talking=False):
    y += math.sin(t * 3) * 4 * s
    lw = int(6 * s)
    coat, gold, scarf = (34, 58, 112), (232, 186, 70), (214, 52, 52)
    for dx in (-30, 10):
        d.rounded_rectangle([x + dx * s, y - 50 * s, x + (dx + 24) * s, y], int(8 * s), fill=(48, 40, 50), outline=OUT, width=lw)
        d.ellipse([x + (dx - 8) * s, y - 16 * s, x + (dx + 32) * s, y + 6 * s], fill=(60, 36, 24), outline=OUT, width=lw)
    _arms(d, x, y, s, t, pose, coat)
    d.rounded_rectangle([x - 72 * s, y - 190 * s, x + 72 * s, y - 40 * s], int(42 * s), fill=coat, outline=OUT, width=lw)
    for k in range(3):
        for sx in (-22, 22):
            d.ellipse([x + sx * s - 7 * s, y - (150 - k * 36) * s - 7 * s, x + sx * s + 7 * s, y - (150 - k * 36) * s + 7 * s], fill=gold, outline=OUT, width=max(2, lw // 2))
    d.rounded_rectangle([x - 62 * s, y - 196 * s, x + 62 * s, y - 166 * s], int(14 * s), fill=scarf, outline=OUT, width=lw)
    d.polygon([(x + 30 * s, y - 172 * s), (x + 58 * s, y - 110 * s), (x + 40 * s, y - 108 * s), (x + 16 * s, y - 170 * s)], fill=scarf, outline=OUT)
    hx, hy, r = x, y - 270 * s, 80 * s
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=SKIN, outline=OUT, width=lw)
    # beard
    beard = (196, 96, 44)
    d.chord([hx - r * 1.02, hy - r * 0.35, hx + r * 1.02, hy + r * 1.25], 0, 180, fill=beard, outline=OUT, width=lw)
    d.ellipse([hx - 34 * s, hy + 22 * s, hx + 34 * s, hy + 60 * s], fill=beard)
    _mouth(d, hx, hy + 44 * s, s, t, expr, talking, 0.9)
    d.ellipse([hx - 16 * s, hy + 2 * s, hx + 16 * s, hy + 30 * s], fill=(244, 160, 130), outline=OUT, width=max(2, lw // 2))   # nose
    _eyes(d, hx, hy - 22 * s, s, t, expr, gap=32, size=0.85)
    _brows(d, hx, hy - 56 * s, s, expr, col=(150, 70, 30), w=11)
    # captain hat
    d.rounded_rectangle([hx - 82 * s, hy - 128 * s, hx + 82 * s, hy - 72 * s], int(22 * s), fill=(250, 250, 248), outline=OUT, width=lw)
    d.rectangle([hx - 78 * s, hy - 92 * s, hx + 78 * s, hy - 72 * s], fill=(28, 34, 66))
    d.chord([hx - 70 * s, hy - 92 * s, hx + 92 * s, hy - 56 * s], 180, 360, fill=(18, 18, 28))
    d.regular_polygon((hx, hy - 106 * s, 14 * s), 5, fill=gold, outline=OUT)

# ---------------------------------------------------------------- B: Professor Pip
def professor(d, x, y, s, t, expr="neutral", pose="idle", talking=False):
    y += math.sin(t * 3) * 4 * s
    lw = int(6 * s)
    vest, shirt, tie = (130, 86, 54), (244, 240, 230), (40, 150, 140)
    for dx in (-26, 6):
        d.rounded_rectangle([x + dx * s, y - 40 * s, x + (dx + 20) * s, y], int(8 * s), fill=(70, 70, 86), outline=OUT, width=lw)
        d.ellipse([x + (dx - 8) * s, y - 14 * s, x + (dx + 28) * s, y + 6 * s], fill=(40, 30, 30), outline=OUT, width=lw)
    _arms(d, x, y, s, t, pose, shirt, sh_y=120)
    d.ellipse([x - 78 * s, y - 180 * s, x + 78 * s, y - 24 * s], fill=shirt, outline=OUT, width=lw)
    d.chord([x - 76 * s, y - 170 * s, x + 76 * s, y - 26 * s], 300, 240, fill=vest)
    d.ellipse([x - 78 * s, y - 180 * s, x + 78 * s, y - 24 * s], outline=OUT, width=lw)
    d.polygon([(x - 26 * s, y - 176 * s), (x, y - 164 * s), (x - 26 * s, y - 152 * s)], fill=tie, outline=OUT)
    d.polygon([(x + 26 * s, y - 176 * s), (x, y - 164 * s), (x + 26 * s, y - 152 * s)], fill=tie, outline=OUT)
    hx, hy, r = x, y - 255 * s, 88 * s
    # hair tufts
    for a in range(-3, 4):
        ang = math.radians(-90 + a * 26)
        cx, cy = hx + r * 0.95 * math.cos(ang), hy + r * 0.85 * math.sin(ang) + 10 * s
        d.ellipse([cx - 30 * s, cy - 30 * s, cx + 30 * s, cy + 30 * s], fill=(246, 246, 250), outline=OUT, width=lw)
    d.ellipse([hx - r, hy - r * 0.92, hx + r, hy + r], fill=SKIN, outline=OUT, width=lw)
    d.chord([hx - r * 0.7, hy - r * 0.95, hx + r * 0.7, hy - r * 0.2], 180, 360, fill=SKIN)   # bald top
    for sx in (-1, 1):
        d.ellipse([hx + sx * r * 0.95 - 26 * s, hy - 20 * s, hx + sx * r * 0.95 + 26 * s, hy + 34 * s], fill=(246, 246, 250), outline=OUT, width=lw)
    _eyes(d, hx, hy - 6 * s, s, t, expr, gap=34, size=0.9)
    for sx in (-34, 34):           # big round glasses
        d.ellipse([hx + sx * s - 34 * s, hy - 40 * s, hx + sx * s + 34 * s, hy + 28 * s], outline=(60, 50, 40), width=int(7 * s))
    d.line([(hx - 2 * s, hy - 10 * s), (hx + 2 * s, hy - 10 * s)], fill=(60, 50, 40), width=int(7 * s))
    _brows(d, hx, hy - 52 * s, s, expr, gap=34, col=(220, 220, 228), w=12)
    d.ellipse([hx - 12 * s, hy + 18 * s, hx + 12 * s, hy + 40 * s], fill=(244, 170, 140), outline=OUT, width=max(2, lw // 2))
    # moustache
    d.chord([hx - 46 * s, hy + 34 * s, hx, hy + 62 * s], 180, 360, fill=(246, 246, 250), outline=OUT, width=max(2, lw // 2))
    d.chord([hx, hy + 34 * s, hx + 46 * s, hy + 62 * s], 180, 360, fill=(246, 246, 250), outline=OUT, width=max(2, lw // 2))
    _mouth(d, hx, hy + 64 * s, s, t, expr, talking, 0.7)

# ---------------------------------------------------------------- C: Bolt the robot
def robot(d, x, y, s, t, expr="neutral", pose="idle", talking=False):
    y += math.sin(t * 3) * 4 * s
    lw = int(6 * s)
    metal, dark, glow = (86, 190, 196), (44, 120, 130), (120, 255, 230)
    d.rounded_rectangle([x - 40 * s, y - 40 * s, x + 40 * s, y], int(14 * s), fill=(70, 80, 90), outline=OUT, width=lw)   # wheel base
    d.ellipse([x - 52 * s, y - 24 * s, x - 12 * s, y + 10 * s], fill=(40, 40, 46), outline=OUT, width=lw)
    d.ellipse([x + 12 * s, y - 24 * s, x + 52 * s, y + 10 * s], fill=(40, 40, 46), outline=OUT, width=lw)
    _arms(d, x, y, s, t, pose, metal, sh_y=140, hand=(200, 210, 220))
    d.rounded_rectangle([x - 70 * s, y - 180 * s, x + 70 * s, y - 40 * s], int(30 * s), fill=metal, outline=OUT, width=lw)
    d.rounded_rectangle([x - 36 * s, y - 150 * s, x + 36 * s, y - 90 * s], int(10 * s), fill=dark, outline=OUT, width=max(2, lw // 2))
    for k in range(3):
        on = int(t * 3 + k) % 3 == 0
        d.ellipse([x - 26 * s + k * 20 * s, y - 128 * s, x - 14 * s + k * 20 * s, y - 116 * s], fill=glow if on else (30, 70, 70))
    d.rectangle([x - 80 * s, y - 120 * s, x - 62 * s, y - 60 * s], fill=(150, 100, 60), outline=OUT, width=max(2, lw // 2))   # satchel strap
    d.rounded_rectangle([x + 40 * s, y - 100 * s, x + 96 * s, y - 50 * s], int(10 * s), fill=(170, 116, 70), outline=OUT, width=lw)  # satchel
    d.rectangle([x - 18 * s, y - 196 * s, x + 18 * s, y - 176 * s], fill=dark, outline=OUT, width=max(2, lw // 2))   # neck
    hx, hy = x, y - 270 * s
    d.rounded_rectangle([hx - 100 * s, hy - 80 * s, hx + 100 * s, hy + 80 * s], int(40 * s), fill=metal, outline=OUT, width=lw)
    d.rounded_rectangle([hx - 80 * s, hy - 58 * s, hx + 80 * s, hy + 58 * s], int(28 * s), fill=(16, 30, 40), outline=OUT, width=max(2, lw // 2))
    # screen face
    blink = t % 3.4 < 0.12
    for ex in (-34, 34):
        cx = hx + ex * s
        if blink or expr == "happy":
            d.arc([cx - 20 * s, hy - 26 * s, cx + 20 * s, hy + 6 * s], 200, 340, fill=glow, width=int(8 * s))
        else:
            hh = 30 if expr != "shocked" else 38
            d.rounded_rectangle([cx - 14 * s, hy - hh * s, cx + 14 * s, hy + 4 * s], int(12 * s), fill=glow)
    if expr == "worried":
        d.line([(hx - 54 * s, hy - 44 * s), (hx - 18 * s, hy - 36 * s)], fill=glow, width=int(5 * s))
        d.line([(hx + 18 * s, hy - 36 * s), (hx + 54 * s, hy - 44 * s)], fill=glow, width=int(5 * s))
    if expr == "shocked":
        d.ellipse([hx - 12 * s, hy + 18 * s, hx + 12 * s, hy + 42 * s], outline=glow, width=int(5 * s))
    elif talking and int(t * 9) % 2 == 0:
        d.rounded_rectangle([hx - 24 * s, hy + 20 * s, hx + 24 * s, hy + 40 * s], int(8 * s), fill=glow)
    else:
        d.arc([hx - 26 * s, hy + 6 * s, hx + 26 * s, hy + 38 * s], 20, 160, fill=glow, width=int(6 * s))
    for sx in (-1, 1):
        d.rounded_rectangle([hx + sx * 100 * s - 14 * s, hy - 26 * s, hx + sx * 100 * s + 14 * s, hy + 26 * s], int(8 * s), fill=dark, outline=OUT, width=max(2, lw // 2))
    d.line([(hx, hy - 80 * s), (hx, hy - 124 * s)], fill=OUT, width=int(6 * s))
    pulse = 0.5 + 0.5 * math.sin(t * 4)
    d.ellipse([hx - 16 * s, hy - 150 * s, hx + 16 * s, hy - 118 * s], fill=(255, int(150 + 80 * pulse), 60), outline=OUT, width=max(2, lw // 2))
    # explorer hat brim
    d.chord([hx - 120 * s, hy - 104 * s, hx + 120 * s, hy - 60 * s], 180, 360, fill=(196, 160, 100), outline=OUT, width=lw)
    d.chord([hx - 74 * s, hy - 150 * s, hx + 74 * s, hy - 70 * s], 180, 360, fill=(214, 178, 116), outline=OUT, width=lw)
    d.rectangle([hx - 72 * s, hy - 96 * s, hx + 72 * s, hy - 84 * s], fill=(120, 80, 50))

STYLES = {"captain": captain, "professor": professor, "robot": robot}

def sheet(path):
    W, H = 1800, 1280
    im = Image.new("RGB", (W, H), (240, 234, 222))
    d = ImageDraw.Draw(im)
    names = [("A", "Captain Finn", "captain", "dengizchi-sayyoh, sarguzasht ruhida"),
             ("B", "Professor Pip", "professor", "olim-ixtirochi, hamma narsani biladi"),
             ("C", "Bolt", "robot", "tarixchi robot, bolalarga ham yoqadi")]
    for i, (lab, nm, st, desc) in enumerate(names):
        cx = 300 + i * 600
        d.rounded_rectangle([cx - 280, 30, cx + 280, 1250], 30, fill=(250, 248, 242), outline=(200, 190, 175), width=4)
        d.text((cx, 80), f"{lab}.  {nm}", font=font(54), fill=(40, 34, 50), anchor="mm")
        d.text((cx, 130), desc, font=font(28), fill=(110, 100, 110), anchor="mm")
        STYLES[st](d, cx, 760, 1.35, 0.6, "neutral", "wave", False)
        for k, ex in enumerate(["happy", "shocked", "thinking"]):
            sx = cx - 180 + k * 180
            STYLES[st](d, sx, 1170, 0.55, 1.7, ex, "panic" if ex == "shocked" else ("point" if ex == "happy" else "think"), False)
    im.save(path)

if __name__ == "__main__":
    import sys
    sheet(sys.argv[1] if len(sys.argv) > 1 else "mascots.png")
