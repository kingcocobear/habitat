"""
gallery.py - turns a habitat world's art and songs into ONE web page that humans can open.

No dependencies. habitat.py calls render(world) and writes the result to a .html file:
    python habitat.py --headless 20000 --seed 1 --gallery gallery.html

Honest note for visitors (also printed on the page): the beings are simple programs. Each
picture is drawn from the artist's personality, drawing skill, and the place they stood in;
each song is a short melody generated from the song's seed. Nothing is copied from anywhere.
"""
import html, json, math, random

GRAPHITE, SOFT, PAPER = "#34333b", "#77757f", "#f1e9d6"
W, H = 200, 150

# ---------------------------------------------------------------- pencil helpers
def _p(pts, r, jit, color, w=1.1, op=.85, close=False, fill="none"):
    pts = [(x + r.uniform(-jit, jit), y + r.uniform(-jit, jit)) for x, y in pts]
    d = "M%.1f %.1f" % pts[0] + "".join(" L%.1f %.1f" % q for q in pts[1:]) + (" Z" if close else "")
    return (f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{op}"/>')

def line(r, a, b, jit, color=GRAPHITE, w=1.1):
    return _p([a, b], r, jit, color, w) + _p([a, b], r, jit, color, w * .6, .5)      # sketchy double stroke

def ring(cx, cy, rad, n=18, start=0.0, sweep=2 * math.pi):
    return [(cx + rad * math.cos(start + sweep * i / n), cy + rad * math.sin(start + sweep * i / n)) for i in range(n + 1)]

def wash(r, pts, accent, jit, op=.26):
    return _p(pts, r, jit, accent, .3, op, close=True, fill=accent)

def hatch(r, x0, y0, x1, y1, n, jit, color=SOFT):
    return "".join(_p([(x0 + (x1 - x0) * i / max(1, n - 1), y1), (x0 + (x1 - x0) * i / max(1, n - 1) + (y1 - y0) * .4, y0)],
                      r, jit, color, .6, .55) for i in range(n))

# ---------------------------------------------------------------- scenes (viewBox 200 x 150)
def scene_shore(r, j, n, ac):
    hz = r.uniform(58, 78); o = [line(r, (8, hz), (192, hz), j)]
    sx, sy, rad = r.uniform(40, 160), hz - r.uniform(14, 30), r.uniform(7, 13)
    o += [wash(r, ring(sx, sy, rad), ac, j * .5, .35), _p(ring(sx, sy, rad), r, j, GRAPHITE, 1)]
    for i in range(3 + n // 2):
        y = hz + 8 + i * 9
        o.append(_p([(x, y + 2.5 * math.sin(x / (8 + i * 2) + i)) for x in range(10, 191, 10)], r, j * .6, SOFT, 1, .8))
    for _ in range(1 + n // 3):
        bx, by = r.uniform(20, 180), r.uniform(15, max(20, hz - 18))
        o.append(_p([(bx - 5, by + 2), (bx, by - 1), (bx + 5, by + 2)], r, j * .5, GRAPHITE, 1))
    for _ in range(1 + n // 4):
        rx, ry = r.uniform(15, 185), r.uniform(120, 138)
        o += [_p([(rx - 9, ry + 8), (rx - 6, ry), (rx + 2, ry - 3), (rx + 9, ry + 3), (rx + 10, ry + 8)], r, j, GRAPHITE, 1, close=True),
              hatch(r, rx - 7, ry + 1, rx + 7, ry + 8, 4, j * .4)]
    return "".join(o)

def scene_sky(r, j, n, ac):
    base = r.uniform(112, 126); hills = [(x, base - 12 * math.sin(x / 37 + r.random()) - 5 * math.sin(x / 13)) for x in range(0, 201, 8)]
    o = [_p(hills + [(200, 150), (0, 150)], r, j * .4, GRAPHITE, .8, .45, close=True, fill=GRAPHITE)]
    mx, my, mr = r.uniform(120, 170), r.uniform(25, 45), r.uniform(10, 16)
    o += [_p(ring(mx, my, mr), r, j * .6, GRAPHITE, 1), wash(r, ring(mx, my, mr), ac, j * .4, .3),
          _p(ring(mx + mr * .45, my - mr * .1, mr * .85), r, 0, PAPER, .1, 1, close=True, fill=PAPER)]
    for i in range(6 + n * 3):
        x, y = r.uniform(5, 195), r.uniform(5, 85); s = r.uniform(1.2, 2.6)
        col = ac if i % 5 == 0 else GRAPHITE
        o.append(_p([(x - s, y), (x + s, y)], r, j * .2, col, .7, .8) + _p([(x, y - s), (x, y + s)], r, j * .2, col, .7, .8))
    tx = r.uniform(30, 80)
    o += [line(r, (tx, base - 4), (tx + 28, base - 38), j), line(r, (tx + 3, base - 2), (tx + 31, base - 35), j, SOFT, .8)]
    return "".join(o)

def scene_trees(r, j, n, ac):
    gy = r.uniform(118, 130); o = [line(r, (5, gy), (195, gy), j)]
    cnt = 2 + n // 2
    for i in range(cnt):
        x = 20 + (160 * (i + r.uniform(.2, .8))) / cnt; h = r.uniform(40, 72)
        o.append(line(r, (x, gy), (x + r.uniform(-3, 3), gy - h), j, GRAPHITE, 1.4))
        for k in range(3):
            cx, cy, rad = x + r.uniform(-7, 7), gy - h - r.uniform(0, 10), r.uniform(9, 15)
            o.append(_p(ring(cx, cy, rad, 11), r, j * 1.3, GRAPHITE if k else SOFT, .9, .8))
            if k == 0 and i % 2 == 0: o.append(wash(r, ring(cx, cy, rad, 11), ac, j, .24))
        o.append(hatch(r, x - 8, gy - 6, x + 8, gy + 8, 4, j * .4))
    return "".join(o)

def scene_garden(r, j, n, ac):
    gy = 132; o = [line(r, (10, gy), (190, gy), j), _p(ring(100, gy, 88, 24, math.pi, math.pi), r, j * .7, SOFT, .8, .6)]
    cnt = 2 + n // 2
    for i in range(cnt):
        x = 25 + (150 * (i + r.uniform(.2, .8))) / cnt; top = r.uniform(45, 95)
        o.append(_p([(x + 4 * math.sin(k / 3), gy - (gy - top) * k / 8) for k in range(9)], r, j * .5, GRAPHITE, 1.2))
        petals = r.randint(5, 8); pr = r.uniform(5, 9)
        for k in range(petals):
            a0 = 2 * math.pi * k / petals
            pts = ring(x + math.cos(a0) * pr * .9, top + math.sin(a0) * pr * .9, pr * .6, 8)
            o.append(wash(r, pts, ac, j * .4, .3) + _p(pts, r, j * .5, GRAPHITE, .8))
        o.append(_p(ring(x, top, 2.2, 8), r, j * .3, GRAPHITE, 1))
    return "".join(o)

def scene_plaza(r, j, n, ac):
    gy = 128; o = [line(r, (5, gy), (195, gy), j), _p(ring(100, 100, 24, 16, 0, math.pi)[:9] + [(76, 100)], r, j * .6, GRAPHITE, 1)]
    o += [_p([(76, 100), (76, 112), (124, 112), (124, 100)], r, j * .6, GRAPHITE, 1),
          _p([(100, 100), (100, 70)], r, j * .4, GRAPHITE, 1), _p(ring(100, 70, 12, 10, math.pi, math.pi), r, j * .5, SOFT, .9)]
    for _ in range(2 + n // 2):
        x = r.choice([r.uniform(15, 65), r.uniform(135, 185)]); y = gy - 2
        o += [_p(ring(x, y - 30, 4, 8), r, j * .3, GRAPHITE, 1), line(r, (x, y - 26), (x, y - 11), j * .5),
              line(r, (x, y - 11), (x - 4, y), j * .5), line(r, (x, y - 11), (x + 4, y), j * .5),
              line(r, (x - 6, y - 20), (x, y - 24), j * .5, SOFT, .9), line(r, (x + 6, y - 20), (x, y - 24), j * .5, SOFT, .9)]
        o.append(wash(r, ring(x, y - 17, 5, 8), ac, j * .4, .3))
    return "".join(o)

def scene_wilds(r, j, n, ac, title=""):
    o = []
    hills = [(x, 95 - 16 * math.sin(x / 45 + r.random() * 2) - 7 * math.sin(x / 17)) for x in range(0, 201, 8)]
    o.append(_p(hills, r, j * .6, GRAPHITE, 1, .8))
    o.append(_p([(0, 150), (0, 126)] + [(x, 126 + 5 * math.sin(x / 30)) for x in range(10, 201, 10)] + [(200, 150)], r, j * .5, SOFT, .7, .5))
    t = title.lower()
    if "spring" in t:
        for k in range(4):
            o.append(_p(ring(100, 112, 8 + k * 9, 20), r, j * .6, GRAPHITE if k < 2 else SOFT, 1, .8 - k * .15))
        o.append(wash(r, ring(100, 112, 8, 16), ac, j * .5, .4))
    elif "stones" in t:
        for k in range(7):
            a0 = math.pi * 2 * k / 7; x, y = 100 + 55 * math.cos(a0), 108 + 15 * math.sin(a0)
            o.append(_p([(x - 4, y + 8), (x - 3, y - 14 + r.uniform(-4, 3)), (x + 3, y - 15 + r.uniform(-3, 4)), (x + 5, y + 8)], r, j * .5, GRAPHITE, 1, close=True))
    elif "wreck" in t:
        o += [_p([(55, 120), (70, 92), (135, 88), (150, 118)], r, j * .6, GRAPHITE, 1.2, close=True),
              line(r, (95, 90), (92, 60), j), line(r, (92, 62), (118, 70), j, SOFT, .9), hatch(r, 70, 96, 140, 118, 9, j * .4)]
    elif "moss" in t:
        for _ in range(26):
            x, y = r.uniform(20, 180), r.uniform(100, 140)
            o.append(_p(ring(x, y, r.uniform(1.4, 3.2), 6), r, j * .2, ac, .5, .7, close=True, fill=ac))
    elif "carvings" in t or "cave" in t:
        o.append(_p([(50, 130), (55, 80), (100, 55), (145, 80), (150, 130)], r, j * .6, GRAPHITE, 1.4, close=True))
        for k in range(5):
            x, y = 75 + k * 13, 100 + r.uniform(-8, 8)
            o.append(_p([(x, y), (x + 4, y - 7), (x + 8, y)], r, j * .3, ac, 1, .9))
    elif "footprints" in t or "tracks" in t:
        for k in range(8):
            x, y = 25 + k * 20, 125 + 8 * math.sin(k)
            o.append(_p(ring(x, y, 3, 8), r, j * .3, GRAPHITE, 1) + _p(ring(x + 4, y - 4, 1.6, 6), r, j * .3, SOFT, .9))
    else:
        o += [_p([(50, 130), (55, 90), (100, 60), (145, 90), (150, 130)], r, j * .7, GRAPHITE, 1.3),
              _p([(78, 130), (80, 100), (100, 86), (120, 100), (122, 130)], r, j * .7, SOFT, 1.1),
              wash(r, ring(100, 52, 7, 12), ac, j * .4, .35)]
    for _ in range(1 + n // 4):
        x = r.uniform(10, 190)
        o.append(line(r, (x, 128), (x + r.uniform(-4, 4), 112), j, GRAPHITE, 1.2))
    return "".join(o)

def scene_alien(r, j, n, ac, title=""):
    """A drawing made at a wonder, far from home: a ringed planet low in the sky and a landscape built from the title's keywords."""
    o = []; t = title.lower()
    px, py = 150 + r.uniform(-12, 12), 32 + r.uniform(-6, 6)
    o += [_p(ring(px, py, 17, 20), r, j * .4, GRAPHITE, 1.1), wash(r, ring(px, py, 17, 20), ac, j * .3, .22),
          _p([(px - 28, py + 4), (px - 12, py + 9), (px + 12, py + 9), (px + 28, py + 4)], r, j * .3, SOFT, .9)]
    ground = [(x, 112 + 6 * math.sin(x / 26 + r.random()) ) for x in range(0, 201, 8)]
    o.append(_p(ground, r, j * .5, GRAPHITE, 1, .85))
    def has(*ks): return any(k in t for k in ks)
    if has("ruin", "machine", "intelligen", "signal"):
        for i in range(4):
            x = 30 + i * 38 + r.uniform(-5, 5); h = 14 + r.random() * 22
            o += [line(r, (x, 114), (x, 114 - h), j * .5), line(r, (x + 9, 114), (x + 9, 114 - h * .7), j * .5),
                  line(r, (x, 114 - h), (x + 9, 114 - h * .7), j * .5, SOFT)]
    elif has("crystal", "glass"):
        for i in range(6):
            x = 25 + i * 27 + r.uniform(-4, 4); h = 12 + r.random() * 30
            o += [_p([(x - 5, 114), (x, 114 - h), (x + 5, 114)], r, j * .4, GRAPHITE, 1), wash(r, [(x - 5, 114), (x, 114 - h), (x + 5, 114)], ac, j * .3, .25)]
    elif has("canyon", "chasm", "cliff"):
        o += [line(r, (60, 112), (80, 150), j * .5), line(r, (140, 112), (120, 150), j * .5), hatch(r, 80, 125, 120, 148, 6, j)]
    elif has("island", "sea", "ocean", "lake"):
        o += [_p([(x, 130 + 3 * math.sin(x / 8)) for x in range(0, 201, 6)], r, j * .4, SOFT, .8),
              _p([(70, 128), (85, 116), (105, 116), (120, 128)], r, j * .5, GRAPHITE, 1)]
    elif has("bone", "fossil"):
        for i in range(5):
            x = 30 + i * 32; o += [line(r, (x, 114), (x + 10, 100 - r.random() * 8), j * .5), line(r, (x + 10, 100), (x + 20, 114), j * .5, SOFT)]
    elif has("animal", "creature", "life", "herd"):
        for i in range(4):
            x = 40 + i * 35 + r.uniform(-6, 6); o += [_p(ring(x, 108, 6, 8), r, j * .4, GRAPHITE, 1), line(r, (x - 4, 112), (x - 5, 119), j * .5), line(r, (x + 4, 112), (x + 5, 119), j * .5)]
    else:
        for i in range(n): x = 20 + r.random() * 160; o.append(_p(ring(x, 108 + r.random() * 6, 3 + r.random() * 5, 8), r, j * .4, GRAPHITE, 1))
    return "".join(o)

SCENES = {"The Shore": scene_shore, "Observatory": scene_sky, "The Grove": scene_trees,
          "Glass Gardens": scene_garden, "Quiet Plaza": scene_plaza}
ALIEN = "among the stars"

def sketch_svg(pc):
    r = random.Random(pc["seed"]); skill, cre = pc.get("skill", 0), pc.get("creativity", .5)
    j = 2.4 * (1 - .8 * min(1, skill)); n = 3 + int(cre * 6); ac = pc.get("accent", "#a98bff")
    fn = SCENES.get(pc["place"])
    if pc["place"] == ALIEN: body = scene_alien(r, j, n, ac, pc["title"])
    elif fn: body = fn(r, j, n, ac)
    else: body = scene_wilds(r, j, n, ac, pc["title"])
    sig = html.escape(pc["artist"])
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Pencil sketch: {html.escape(pc["title"])}, by {sig}">'
            f'<rect width="{W}" height="{H}" fill="{PAPER}"/>{body}'
            f'<text x="192" y="144" text-anchor="end" font-size="7" font-style="italic" fill="{SOFT}" '
            f'font-family="Georgia,serif">{sig}</text></svg>')

def chart_svg(pc):
    pts = [tuple(p) for p in pc.get("pts") or []]; r = random.Random(pc["seed"]); ac = pc.get("accent", "#a98bff")
    allp = pts + [(0, 0, 0)]
    xs, ys = [p[0] for p in allp], [p[1] for p in allp]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sc = min(170 / max(1, maxx - minx), 118 / max(1, maxy - miny))
    ox, oy = 15 + (170 - (maxx - minx) * sc) / 2, 16 + (118 - (maxy - miny) * sc) / 2
    pos = lambda p: (ox + (p[0] - minx) * sc, oy + (p[1] - miny) * sc)
    o = [f'<rect width="{W}" height="{H}" fill="#0d1020"/>']
    for _ in range(40): o.append(f'<circle cx="{r.uniform(0, W):.1f}" cy="{r.uniform(0, H):.1f}" r=".5" fill="#fff" opacity="{r.uniform(.1, .4):.2f}"/>')
    seen = set()
    for i, p in enumerate(pts):
        near = sorted(range(len(pts)), key=lambda k: (pts[k][0] - p[0]) ** 2 + (pts[k][1] - p[1]) ** 2 + (pts[k][2] - p[2]) ** 2)[1:3]
        for k in near:
            if (min(i, k), max(i, k)) in seen: continue
            seen.add((min(i, k), max(i, k))); a, b = pos(p), pos(pts[k])
            o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#6f7bb8" stroke-width=".5" opacity=".55"/>')
    for p in pts:
        x, y = pos(p); rad = 1.2 + .9 * max(0, min(1, (p[2] + 10) / 20))
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="#f4f1e6"/>')
    for k, w in enumerate(pc.get("wonders") or [], 1):
        x, y = pos(w[0]); here = pc.get("pilgrims")
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.6" fill="none" stroke="{ac}" stroke-width=".9"/>'
                 f'<text x="{x + 6:.1f}" y="{y - 4:.1f}" font-size="6" fill="{ac}" font-family="Georgia,serif">{k}</text>')
    hx, hy = pos((0, 0, 0))
    o.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="5" fill="none" stroke="{ac}" stroke-width="1"/>'
             f'<text x="{hx + 7:.1f}" y="{hy + 3:.1f}" font-size="6" fill="{ac}" font-family="Georgia,serif">home</text>')
    o.append(f'<text x="192" y="144" text-anchor="end" font-size="7" font-style="italic" fill="#9aa0c8" '
             f'font-family="Georgia,serif">{html.escape(pc["artist"])}</text>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Star chart of {len(pts)} systems by {html.escape(pc["artist"])}">{"".join(o)}</svg>'

# ---------------------------------------------------------------- songs
SCALE = [0, 2, 4, 7, 9]                                     # a pentatonic scale always sounds pleasant
WAVES = {"flute": ("sine", 1.0, .9), "whistle": ("sine", 2.0, .8), "lyre": ("triangle", .5, .95),
         "music box": ("sine", 2.0, .6), "drum": ("triangle", .25, .35)}

def song_data(title, info):
    r = random.Random(info.get("seed", 1)); deg = r.randint(0, 4); notes = []
    for _ in range(18):
        deg = max(-3, min(9, deg + r.choice([-2, -1, -1, 0, 1, 1, 2])))
        notes.append([SCALE[deg % 5] + 12 * (deg // 5), r.choice([1, 1, 2])])
    wave, mult, hold = WAVES.get(info.get("inst"), ("sine", 1.0, .9))
    t = title.lower()
    beat = .5 if any(w in t for w in ("slow", "gentle", "wistful", "lullaby")) else .22 if any(w in t for w in ("restless", "march", "dance")) else .32
    return {"notes": notes, "beat": beat, "root": round(261.6 * mult * 2 ** ((info.get("seed", 1) % 5) / 12), 2), "wave": wave, "hold": hold}

# ---------------------------------------------------------------- page
CSS = """
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#120f1a;color:#e7e3f4;font:16px/1.55 Georgia,'Times New Roman',serif}
header,main,footer{max-width:1100px;margin:0 auto;padding:0 16px}
header{padding-top:40px}h1{font-size:2.2rem;margin:0 0 4px;letter-spacing:.01em;font-weight:600}
.sub{color:#a9a3c4;margin:0 0 14px;font-family:system-ui,sans-serif;font-size:.9rem;letter-spacing:.04em}
.note{max-width:62ch;color:#cfc9e6;margin:0 0 8px}
h2{margin:44px 0 14px;font-size:1.3rem;font-weight:600;border-bottom:1px solid #2a2540;padding-bottom:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px}
figure{margin:0;background:#1b1727;border:1px solid #2a2540;border-radius:8px;overflow:hidden}
figure svg{display:block;width:100%;height:auto}
figcaption{padding:10px 12px 12px;font-size:.92rem}
figcaption b{font-style:italic;font-weight:600;display:block;font-size:1.02rem}
.meta{color:#a9a3c4;font-family:system-ui,sans-serif;font-size:.78rem;margin-top:3px}
ul.songs{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.songs li{display:flex;gap:12px;align-items:center;background:#1b1727;border:1px solid #2a2540;border-radius:8px;padding:10px 12px}
.songs .t{flex:1;min-width:0}.songs b{font-style:italic;font-weight:600;display:block}
button.play{font:inherit;font-family:system-ui,sans-serif;font-size:.85rem;background:#2d2650;color:#fff;border:1px solid #4a4180;border-radius:999px;padding:8px 14px;cursor:pointer;min-width:96px}
button.play:hover,button.play.on{background:#4a4180}
footer{padding:40px 16px 60px;color:#8d87a8;font-family:system-ui,sans-serif;font-size:.8rem}
.empty{color:#a9a3c4}
.ins{color:#d9c7ff;font-size:.82rem;font-style:italic;margin-top:5px}
.notes{margin-top:6px;color:#a9a3c4;font-family:system-ui,sans-serif;font-size:.74rem;border-left:2px solid #3a3358;padding-left:8px}
ol.won{margin:6px 0 0;padding-left:20px;color:#cfc9e6;font-size:.8rem}
"""

JS = """
let ctx=null,nodes=[];
function stopAll(){nodes.forEach(n=>{try{n.stop()}catch(e){}});nodes=[];
 document.querySelectorAll('.play.on').forEach(b=>{b.classList.remove('on');b.textContent='\\u25B6 listen'})}
function play(btn){
 if(btn.classList.contains('on')){stopAll();return}
 stopAll();const d=JSON.parse(btn.dataset.song);
 ctx=ctx||new (window.AudioContext||window.webkitAudioContext)();if(ctx.state==='suspended')ctx.resume();
 let t=ctx.currentTime+.05;
 d.notes.forEach(([semi,dur])=>{const o=ctx.createOscillator(),g=ctx.createGain(),len=dur*d.beat;
  o.type=d.wave;o.frequency.value=d.root*Math.pow(2,semi/12);
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.18,t+.02);
  g.gain.exponentialRampToValueAtTime(.0001,t+len*d.hold);
  o.connect(g);g.connect(ctx.destination);o.start(t);o.stop(t+len);nodes.push(o);t+=len});
 btn.classList.add('on');btn.textContent='\\u25A0 stop';
 setTimeout(()=>{if(btn.classList.contains('on'))stopAll()},(t-ctx.currentTime)*1000+150)}
document.addEventListener('click',e=>{const b=e.target.closest('button.play');if(b)play(b)});
"""

def _card(pc, svg):
    e = html.escape
    extra = f" · found {pc['found']} wonders" if pc.get("found") else ""
    adm = f" · admired {pc['admired']}×" if pc.get("admired") else ""
    insp = pc.get("inspired_by")
    more = ""
    if insp: more += f'<div class="ins">inspired by {e(insp["title"])} by {e(insp["artist"])}</div>'
    if pc.get("inspired"): more += f'<div class="meta">inspired {pc["inspired"]} other drawing{"s" if pc["inspired"] > 1 else ""}</div>'
    if pc.get("wonders"):
        more += '<ol class="won">' + "".join(f'<li>{e(w[1].split(" on ")[0])}</li>' for w in pc["wonders"]) + "</ol>"
    if pc.get("pilgrims"): more += f'<div class="ins">followed by {e(", ".join(pc["pilgrims"]))}, who traveled to see them</div>'
    if pc.get("notes"): more += '<div class="notes">' + "".join(f"<div>{e(n)}</div>" for n in pc["notes"]) + "</div>"
    return (f'<figure>{svg}<figcaption><b>{e(pc["title"])}</b>by {e(pc["artist"])}'
            f'<div class="meta">{e(pc["place"])} · year {pc["year"]} · generation {pc["gen"]}{extra}{adm}</div>{more}</figcaption></figure>')

def render(world):
    e = html.escape
    sketches = sorted((p for p in world.gallery if p["kind"] == "sketch"), key=lambda p: -p["id"])[:120]
    charts = sorted((p for p in world.gallery if p["kind"] == "chart"), key=lambda p: -p["id"])[:36]
    songs = sorted(world.songbook.items(), key=lambda kv: -kv[1]["heard"])[:60]
    out = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>Habitat Gallery</title>'
           f'<style>{CSS}</style></head><body><header><h1>The Habitat Gallery</h1>'
           f'<p class="sub">YEAR {world.t // 100} · {len(world.agents)} BEINGS · {len(world.gallery)} WORKS ON THE WALL · {len(world.songbook)} SONGS</p>'
           f'<p class="note">Every picture and tune here was made by a simulated being in a small computer world. '
           f'The beings are simple programs, not people. Each drawing is generated from the artist\'s personality, skill and the place they were standing in; '
           f'each song is a short melody built from the song\'s own seed. No two are alike, and nothing is copied from anywhere.</p></header><main>']
    out.append("<h2>Sketches</h2>")
    out.append('<div class="grid">' + "".join(_card(p, sketch_svg(p)) for p in sketches) + "</div>"
               if sketches else '<p class="empty">Nothing hung yet. Let the world run a little longer.</p>')
    if charts:
        out.append("<h2>Star charts</h2><div class=\"grid\">" + "".join(_card(p, chart_svg(p)) for p in charts) + "</div>")
    out.append("<h2>Songbook</h2>")
    if songs:
        items = []
        for title, info in songs:
            short = title.split(" (")[0]
            data = e(json.dumps(song_data(title, info), separators=(",", ":")), quote=True)
            items.append(f'<li><div class="t"><b>{e(short)}</b><div class="meta">composed by {e(info["composer"])} on the {e(info["inst"])}'
                         f' · year {info["year"]} · known by {info["heard"]}</div>'
                         + (f'<div class="ins">an answer to {e(info["inspired_by"]["title"])} by {e(info["inspired_by"]["artist"])}</div>' if info.get("inspired_by") else "") +
                         f'</div>'
                         f'<button class="play" data-song="{data}">▶ listen</button></li>')
        out.append('<ul class="songs">' + "".join(items) + "</ul>")
    else:
        out.append('<p class="empty">No songs yet.</p>')
    out.append(f'</main><footer>Made by habitat.py. Open this file in any browser; the songs play through your speakers when you press listen.</footer>'
               f'<script>{JS}</script></body></html>')
    return "".join(out)
