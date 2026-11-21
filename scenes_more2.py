"""Scenes for: AI data centers, self-driving sensors, why the sky is blue."""
import math, random
import make_video as mv
from tech_scenes import _car, _skyline
from scenes_more import _txt

def lm_servers(img, d, cx, by, sc, ctx, hot=False):
    rack, slot, led = sc((44, 50, 70)), sc((70, 78, 104)), sc((92, 240, 140))
    for k in range(3):
        x0 = cx - 390 + k * 270
        d.rounded_rectangle([x0, by - 760, x0 + 230, by], 18, fill=rack)
        for j in range(12):
            y = by - 730 + j * 58
            d.rounded_rectangle([x0 + 18, y, x0 + 212, y + 44], 8, fill=slot)
            d.ellipse([x0 + 30, y + 15, x0 + 44, y + 29], fill=led if (j + k) % 3 else sc((255, 206, 84)))
            d.rectangle([x0 + 120, y + 18, x0 + 196, y + 26], fill=sc((40, 46, 64)))
    if hot:
        heat = sc((255, 110, 80))
        for k in range(5):
            x = cx - 330 + k * 165
            pts = [(x + 26 * math.sin(i / 3), by - 790 - i * 18) for i in range(12)]
            d.line(pts, fill=heat, width=14, joint="curve")
        _txt(d, cx, by - 1110, "HOT!", 120, (255, 110, 80))

def lm_cooling(img, d, cx, by, sc, ctx):
    lm_servers(img, d, cx, by, sc, ctx)
    water = sc((80, 190, 255))
    d.rectangle([cx - 470, by - 820, cx + 470, by - 790], fill=water)
    for k in range(4):
        x = cx - 430 + k * 270
        d.rectangle([x, by - 790, x + 22, by], fill=water)
    for k in range(9):
        x = cx - 440 + k * 110
        d.ellipse([x, by - 840, x + 40, by - 800], fill=sc((200, 236, 255)))
    # cooling tower with steam
    tx = cx + 520
    d.polygon([(tx - 80, by), (tx + 80, by), (tx + 55, by - 420), (tx - 55, by - 420)], fill=sc((214, 220, 232)))
    for i in range(4):
        r = 50 + i * 22
        d.ellipse([tx - r, by - 470 - i * 70 - r, tx + r, by - 470 - i * 70 + r], fill=sc((240, 244, 250)))

def lm_power(img, d, cx, by, sc, ctx):
    _skyline(d, cx, by, sc, seed=31, hmax=520)
    # big bolt over the city = how much electricity
    y0 = by - 1000
    d.polygon([(cx + 60, y0), (cx - 120, y0 + 330), (cx - 10, y0 + 330), (cx - 80, y0 + 600),
               (cx + 140, y0 + 230), (cx + 30, y0 + 230)], fill=(255, 220, 80))

def lm_selfdrive(img, d, cx, by, sc, ctx, rings=True):
    d.rectangle([cx - 700, by - 20, cx + 700, by + 80], fill=sc((48, 52, 66)))
    for x in range(int(cx - 700), int(cx + 700), 120):
        d.rectangle([x, by + 22, x + 60, by + 32], fill=sc((236, 236, 236)))
    _car(d, cx - 90, by, sc, col=(236, 240, 246), s=0.9)
    top = by - 70 * 0.9 - 120 * 0.9 - 96 * 0.9
    cx = cx - 90
    d.rounded_rectangle([cx - 40, top - 56, cx + 40, top], 14, fill=sc((40, 44, 56)))
    d.ellipse([cx - 30, top - 86, cx + 30, top - 46], fill=sc((80, 200, 255)))
    if rings:
        for i, r in enumerate((220, 360, 500)):
            d.arc([cx - r, top - 66 - r * 0.45, cx + r, top - 66 + r * 0.45], 180, 360, fill=sc((80, 200, 255)), width=10 - i * 2)
    # pedestrian ahead
    px = cx + 420
    d.ellipse([px - 34, by - 300, px + 34, by - 232], fill=sc((255, 206, 84)))
    d.rounded_rectangle([px - 40, by - 228, px + 40, by - 80], 20, fill=sc((226, 76, 70)))
    d.rectangle([px - 34, by - 84, px - 10, by - 20], fill=sc((40, 44, 56)))
    d.rectangle([px + 10, by - 84, px + 34, by - 20], fill=sc((40, 44, 56)))

def lm_sensors(img, d, cx, by, sc, ctx):
    items = [("CAMERA", "sees colors & signs", (80, 170, 255)),
             ("RADAR", "speed, rain or fog", (92, 230, 150)),
             ("LIDAR", "3D laser map", (255, 206, 84))]
    for i, (name, sub, col) in enumerate(items):
        y = by - 860 + i * 270
        d.rounded_rectangle([cx - 400, y, cx + 400, y + 220], 36, fill=sc((36, 42, 62)))
        d.ellipse([cx - 370, y + 40, cx - 230, y + 180], fill=sc(col))
        _txt(d, cx - 190, y + 78, name, 74, (255, 255, 255), "lm")
        _txt(d, cx - 190, y + 156, sub, 48, sc((180, 190, 214)), "lm")

def lm_pointcloud(img, d, cx, by, sc, ctx):
    rnd = random.Random(7)
    d.rounded_rectangle([cx - 420, by - 900, cx + 420, by - 60], 40, fill=(14, 18, 30))
    def pts_box(x0, y0, w, h, n, col):
        for _ in range(n):
            x, y = x0 + rnd.random() * w, y0 + rnd.random() * h
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=col)
    for k in range(8):                          # road lines of dots
        y = by - 160 - k * 40
        for x in range(int(cx - 380 + k * 30), int(cx + 380 - k * 30), 26):
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(60, 90, 150))
    pts_box(cx - 300, by - 560, 260, 180, 260, (80, 200, 255))       # car
    pts_box(cx + 120, by - 640, 70, 260, 160, (255, 206, 84))        # person
    pts_box(cx - 380, by - 860, 140, 340, 200, (92, 230, 150))       # tree / pole

def lm_sunrays(img, d, cx, by, sc, ctx, sunset=False):
    sx, sy = cx - 360, by - 980
    d.ellipse([sx - 110, sy - 110, sx + 110, sy + 110], fill=(255, 236, 150))
    cols = [(255, 80, 80), (255, 160, 60), (255, 230, 80), (92, 230, 150), (80, 160, 255), (150, 100, 255)]
    for i, c in enumerate(cols):
        a = math.radians(40 + i * 2.2)
        L = 900
        d.line([(sx, sy), (sx + L * math.cos(a), sy + L * math.sin(a))], fill=c, width=12)
    # air molecules scattering blue
    rnd = random.Random(2)
    for _ in range(14):
        x, y = cx - 120 + rnd.random() * 520, by - 760 + rnd.random() * 520
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(236, 240, 248))
        if not sunset:
            for k in range(6):
                b = k / 6 * 6.283
                d.line([(x, y), (x + 70 * math.cos(b), y + 70 * math.sin(b))], fill=(90, 160, 255), width=6)

def lm_waves(img, d, cx, by, sc, ctx):
    d.rounded_rectangle([cx - 430, by - 820, cx + 430, by - 120], 40, fill=(20, 26, 42))
    for row, (col, wl, label) in enumerate([((80, 160, 255), 70, "BLUE  short waves"), ((255, 90, 80), 190, "RED  long waves")]):
        y = by - 640 + row * 320
        pts = [(cx - 380 + i * 4, y + 60 * math.sin((i * 4) / wl * 6.283)) for i in range(191)]
        d.line(pts, fill=col, width=12, joint="curve")
        _txt(d, cx, y + 130, label, 54, col)

def lm_sunset(img, d, cx, by, sc, ctx):
    _skyline(d, cx, by, sc, seed=41, hmax=380)

mv.LANDMARKS.update({
    "servers": lm_servers, "servers_hot": lambda *a: lm_servers(*a, hot=True), "cooling": lm_cooling,
    "power_city": lm_power, "selfdrive": lm_selfdrive, "selfdrive_plain": lambda *a: lm_selfdrive(*a, rings=False),
    "sensors": lm_sensors, "pointcloud": lm_pointcloud,
    "sunrays": lm_sunrays, "sunrays_sunset": lambda *a: lm_sunrays(*a, sunset=True), "waves": lm_waves,
    "skyline_low": lm_sunset,
})
import scenes_more3
