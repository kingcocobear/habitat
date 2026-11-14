"""
perception_test.py - Habitat Perception Experiment 001.

Question: what is the best way to SHOW a habitat place to an AI guest?
The same scene is given four ways, and the AI answers the same questions about it:

  picture   a top-down picture of the place (needs a vision model)
  binary    the same picture, but every square is drawn out of 1s and 0s (needs a vision model)
  grid      a small text map:  # wall  T tree  ~ water  F food  @ another being  A you
  words     a plain description: "a tree 3 steps north and 2 east", like guests get now

For each way it scores: right answers, tokens used, and seconds per answer.
Everything is made up from a seed, so a run can be repeated exactly.

Standard library only. Works with any model:
    python perception_test.py --model gemma3:4b                    (Ollama)
    python perception_test.py --model llava --scenes 20
    python perception_test.py --model qwen2.5:3b --text-only       (a model that can't see pictures)
    python perception_test.py --model MODEL --provider openai --url http://localhost:1234/v1
    python perception_test.py --save-scenes scenes/                (just write the scenes out to look at)
    python perception_test.py --selftest                           (checks the test itself, no model needed)
Results are printed as a table and saved to perception_results.json.
"""
import argparse, base64, json, math, os, random, struct, sys, time, urllib.request, zlib

GW, GH = 15, 11                       # scene size in squares
CELL = 24                             # pixels per square in pictures
DIRS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
NAMES = {"T": "tree", "~": "water", "F": "food", "@": "another being"}
PHRASE = {"T": "a tree", "~": "water", "F": "food", "@": "another being"}
LEGEND = "North is up. # wall, T tree, ~ water, F food, @ another being, A is you, . open ground."
PIC_LEGEND = ("A top-down map, north is up. Dark grey squares are walls, green circles are trees, blue squares are water, "
              "small orange squares are food, purple circles are other beings, and the red circle with a white ring is you.")


# ------------------------------------------------------------------ scenes
def make_scene(seed):
    """A small walled place with trees, a pond, food, other beings and you. Retries until questions are clear."""
    r = random.Random(seed)
    for _ in range(200):
        g = [["#" if x in (0, GW - 1) or y in (0, GH - 1) else "." for x in range(GW)] for y in range(GH)]
        if r.random() < .7:                                   # an inside wall
            if r.random() < .5:
                y = r.randrange(3, GH - 3); x0 = r.randrange(2, GW - 6)
                for x in range(x0, x0 + r.randrange(3, 6)): g[y][x] = "#"
            else:
                x = r.randrange(3, GW - 3); y0 = r.randrange(2, GH - 5)
                for y in range(y0, y0 + r.randrange(2, 4)): g[y][x] = "#"
        px, py = r.randrange(2, GW - 3), r.randrange(2, GH - 3)  # a pond
        for y in range(py, py + r.randrange(1, 3)):
            for x in range(px, px + r.randrange(2, 4)):
                if g[y][x] == ".": g[y][x] = "~"
        def put(ch, n):
            for _ in range(n):
                for _ in range(50):
                    x, y = r.randrange(1, GW - 1), r.randrange(1, GH - 1)
                    if g[y][x] == ".": g[y][x] = ch; break
        put("T", r.randrange(2, 8)); put("F", r.randrange(1, 3)); put("@", r.randrange(1, 4)); put("A", 1)
        sc = dict(seed=seed, grid=["".join(row) for row in g])
        if all(c in "".join(sc["grid"]) for c in "TF~@A"):
            qs = questions(sc, random.Random(seed * 31 + 7))
            if len(qs) >= 4:
                sc["questions"] = qs
                return sc
    raise RuntimeError("could not make a clear scene")


def find(sc, ch):
    return [(x, y) for y, row in enumerate(sc["grid"]) for x, c in enumerate(row) if c == ch]


def compass(dx, dy):                                         # dy grows southward
    ang = math.degrees(math.atan2(dx, -dy)) % 360
    return DIRS[int((ang + 22.5) // 45) % 8]


def questions(sc, r):
    """Multiple-choice questions with known right answers. Only asks ones that have one clear answer."""
    (ax, ay), = find(sc, "A")
    dist = lambda p: math.hypot(p[0] - ax, p[1] - ay)
    near = {ch: min(map(dist, find(sc, ch))) for ch in NAMES if find(sc, ch)}
    qs = []
    def mc(kind, text, right, wrong):
        opts = [right] + [w for w in dict.fromkeys(wrong) if w != right][:3]
        r.shuffle(opts)
        letters = "ABCD"[:len(opts)]
        qs.append(dict(kind=kind, text=text + "\n" + "\n".join(f"{l}) {o}" for l, o in zip(letters, opts)),
                       answer=letters[opts.index(right)], right=right))
    n = len(find(sc, "T"))                                       # 1. counting
    mc("count", "How many trees are there?", str(n), [str(n + d) for d in r.sample([-2, -1, 1, 2, 3], 4) if n + d >= 0])
    ranked = sorted(near, key=near.get)                          # 2. what is nearest (only if clearly nearest)
    if len(ranked) > 1 and near[ranked[1]] - near[ranked[0]] >= 1:
        mc("nearest", "What is closest to you?", NAMES[ranked[0]], [NAMES[c] for c in ranked[1:]])
    food = min(find(sc, "F"), key=dist)                          # 3. direction (skip if right on a boundary)
    dx, dy = food[0] - ax, food[1] - ay
    ang = math.degrees(math.atan2(dx, -dy)) % 360
    if min(abs((ang - 22.5) % 45), abs((ang - 22.5) % 45 - 45)) > 6:
        right = compass(dx, dy); i = DIRS.index(right)
        mc("direction", "In which direction is the nearest food from you?", right,
           [DIRS[(i + k) % 8] for k in r.sample([1, 2, 3, 4, 5, 6, 7], 3)])
    if abs(near["~"] - near["F"]) >= 1.5:                        # 4. comparing distances
        right = "the water" if near["~"] > near["F"] else "the food"
        mc("farther", "Which is farther from you: the nearest water or the nearest food?", right, ["the water", "the food"])
    walls = sum(c == "#" for row in sc["grid"][1:-1] for c in row[1:-1])  # 5. is there an inside wall
    mc("wall", "Is there a wall inside the place (not counting the outer edge)?", "yes" if walls else "no", ["yes", "no"])
    return qs


# ------------------------------------------------------------------ the four ways to show it
def as_grid(sc):
    return LEGEND + "\n" + "\n".join(sc["grid"])


def as_words(sc):
    (ax, ay), = find(sc, "A")
    out = []
    for ch, name in NAMES.items():
        for x, y in sorted(find(sc, ch), key=lambda p: math.hypot(p[0] - ax, p[1] - ay)):
            dx, dy = x - ax, y - ay
            parts = ([f"{-dy} north" if dy < 0 else f"{dy} south"] if dy else []) + \
                    ([f"{dx} east" if dx > 0 else f"{-dx} west"] if dx else [])
            out.append(f"{PHRASE[ch]} {' and '.join(parts)} of you")
    inside = [(x, y) for x, y in find(sc, "#") if 0 < x < GW - 1 and 0 < y < GH - 1]
    walls = f"There is a wall inside the place, along {len(inside)} squares." if inside else "There are no walls inside the place."
    return (f"You are in a walled place {GW - 2} squares wide and {GH - 2} deep. Distances are in steps. "
            f"You can see: " + "; ".join(out) + ". " + walls)


COLORS = {"#": (70, 70, 78), ".": (238, 232, 214), "T": (60, 150, 70), "~": (70, 130, 210),
          "F": (235, 140, 40), "@": (140, 90, 200), "A": (215, 50, 50)}
DIGITS = {"0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"]}


def _canvas(sc):
    return [[COLORS["."]] * (GW * CELL) for _ in range(GH * CELL)]


def as_picture(sc):
    px = _canvas(sc)
    for y, row in enumerate(sc["grid"]):
        for x, ch in enumerate(row):
            for j in range(CELL):
                for i in range(CELL):
                    cx, cy = i - CELL / 2 + .5, j - CELL / 2 + .5; d = math.hypot(cx, cy)
                    col = COLORS["."]
                    if ch in "#~": col = COLORS[ch]
                    elif ch in "T@" and d < CELL * .42: col = COLORS[ch]
                    elif ch == "F" and abs(cx) < CELL * .25 and abs(cy) < CELL * .25: col = COLORS["F"]
                    elif ch == "A": col = COLORS["A"] if d < CELL * .3 else (255, 255, 255) if d < CELL * .45 else col
                    px[y * CELL + j][x * CELL + i] = col
    return png(px)


def as_binary(sc):
    """Every square is a digit: 1s draw the things, dim 0s are the ground. Like a figure made of binary."""
    px = _canvas(sc)
    for y, row in enumerate(sc["grid"]):
        for x, ch in enumerate(row):
            digit = "0" if ch == "." else "1"
            col = (200, 192, 170) if ch == "." else COLORS[ch]
            pat, s = DIGITS[digit], 4                              # 3x5 digit, scaled 4x = 12x20 pixels
            ox, oy = x * CELL + (CELL - 3 * s) // 2, y * CELL + (CELL - 5 * s) // 2
            for j, line in enumerate(pat):
                for i, bit in enumerate(line):
                    if bit == "1":
                        for v in range(s):
                            for u in range(s): px[oy + j * s + v][ox + i * s + u] = col
            if ch == "A":                                          # mark "you" with a ring of 1s around the square
                for k in range(CELL):
                    for p in ((k, 0), (k, CELL - 1), (0, k), (CELL - 1, k)): px[y * CELL + p[1]][x * CELL + p[0]] = COLORS["A"]
    return png(px)


def png(px):
    """Encode rows of (r,g,b) as a PNG file (bytes). No libraries needed."""
    h, w = len(px), len(px[0])
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


WAYS = {
    "picture": lambda sc: (PIC_LEGEND, as_picture(sc)),
    "binary":  lambda sc: (PIC_LEGEND.replace("A top-down map", "A top-down map drawn out of digits: each square is a 1 or a 0; "
                                              "dim 0s are open ground and coloured 1s are things") , as_binary(sc)),
    "grid":    lambda sc: (as_grid(sc), None),
    "words":   lambda sc: (as_words(sc), None),
}


# ------------------------------------------------------------------ asking a model
def make_model(model, provider="ollama", url=None, key_env=None, timeout=180):
    """Returns ask(text, image_png_or_None) -> (reply, tokens_in, tokens_out)."""
    key = os.environ.get(key_env, "") if key_env else ""
    def ask(text, image=None):
        if provider == "ollama":
            msg = {"role": "user", "content": text}
            if image: msg["images"] = [base64.b64encode(image).decode()]
            endpoint = (url or "http://localhost:11434").rstrip("/") + "/api/chat"
            body = {"model": model, "messages": [msg], "stream": False, "options": {"temperature": 0}}
        else:
            content = [{"type": "text", "text": text}]
            if image: content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(image).decode()}})
            endpoint = (url or "http://localhost:1234/v1").rstrip("/") + "/chat/completions"
            body = {"model": model, "messages": [{"role": "user", "content": content}], "temperature": 0}
        headers = {"Content-Type": "application/json"}
        if key: headers["Authorization"] = f"Bearer {key}"
        req = urllib.request.Request(endpoint, json.dumps(body).encode(), headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            d = json.loads(resp.read())
        if provider == "ollama":
            return d["message"]["content"], d.get("prompt_eval_count", 0), d.get("eval_count", 0)
        u = d.get("usage") or {}
        return d["choices"][0]["message"]["content"], u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    return ask


def pick_letter(reply):
    reply = reply.strip().upper()
    for ch in reply[:3]:
        if ch in "ABCD": return ch
    for tok in reply.replace(")", " ").replace(".", " ").split():
        if tok in ("A", "B", "C", "D"): return tok
    return "?"


PROMPT = "{scene}\n\nQuestion: {q}\n\nAnswer with just the letter of the right choice."


def run(ask, seeds, ways, log=print):
    results = []
    for seed in seeds:
        sc = make_scene(seed)
        for way in ways:
            text, image = WAYS[way](sc)
            for q in sc["questions"]:
                t0 = time.time()
                try:
                    reply, tin, tout = ask(PROMPT.format(scene=text, q=q["text"]), image)
                except Exception as e:
                    log(f"  {way} seed {seed}: model error ({e}); skipping this way")
                    break
                got = pick_letter(reply)
                results.append(dict(seed=seed, way=way, kind=q["kind"], right=got == q["answer"], got=got,
                                    answer=q["answer"], tokens_in=tin, tokens_out=tout, seconds=round(time.time() - t0, 2)))
        log(f"scene {seed} done")
    return results


def table(results):
    rows = ["way        right    tokens in  seconds   by question (right/asked)", "-" * 78]
    for way in WAYS:
        rs = [r for r in results if r["way"] == way]
        if not rs: continue
        kinds = {}
        for r in rs: k = kinds.setdefault(r["kind"], [0, 0]); k[0] += r["right"]; k[1] += 1
        acc = sum(r["right"] for r in rs) / len(rs)
        rows.append(f"{way:<10} {acc:>5.0%}  {sum(r['tokens_in'] for r in rs) / len(rs):>10.0f}  "
                    f"{sum(r['seconds'] for r in rs) / len(rs):>7.2f}   " +
                    "  ".join(f"{k} {v[0]}/{v[1]}" for k, v in kinds.items()))
    return "\n".join(rows)


# ------------------------------------------------------------------ checking the test itself
def selftest():
    """Solves every question from the grid text alone; it must get 100%. Also checks pictures and repeatability."""
    ok = 0
    for seed in range(1, 61):
        sc = make_scene(seed)
        assert make_scene(seed) == sc, "same seed must give the same scene"
        grid = as_grid(sc).splitlines()[1:]
        solved = questions(dict(seed=seed, grid=grid), random.Random(seed * 31 + 7))
        assert [q["answer"] for q in solved] == [q["answer"] for q in sc["questions"]], seed
        for q in sc["questions"]:
            assert q["text"].count(")") >= 2 and q["answer"] in "ABCD"
        words = as_words(sc)
        assert words.count("a tree") == len(find(sc, "T")), "words must mention every tree"
        for way in ("picture", "binary"):
            img = WAYS[way](sc)[1]
            assert img[:8] == b"\x89PNG\r\n\x1a\n" and len(img) > 200
        ok += len(sc["questions"])
    fake = lambda text, image=None: (random.choice("ABCD"), len(text) // 4, 1)
    res = run(fake, [1, 2], list(WAYS), log=lambda *a: None)
    assert res and all(r["got"] in "ABCD" for r in res)
    assert pick_letter("B) the food") == "B" and pick_letter("The answer is C.") == "C"
    print(f"selftest ok: 60 scenes, {ok} questions all solvable from the map, pictures valid, scoring works")


def main(argv=None):
    p = argparse.ArgumentParser(description="Habitat Perception Experiment 001")
    p.add_argument("--model")
    p.add_argument("--provider", choices=["ollama", "openai"], default="ollama")
    p.add_argument("--url"); p.add_argument("--key-env")
    p.add_argument("--scenes", type=int, default=10, help="how many scenes (each has 4-5 questions)")
    p.add_argument("--seed", type=int, default=1, help="first scene seed")
    p.add_argument("--ways", default=",".join(WAYS), help="which ways to test, e.g. grid,words")
    p.add_argument("--text-only", action="store_true", help="skip the two picture ways (for models that can't see)")
    p.add_argument("--save-scenes", metavar="DIR", help="write each scene's pictures and texts to a folder")
    p.add_argument("--out", default="perception_results.json")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args(argv)
    if a.selftest: return selftest()
    seeds = list(range(a.seed, a.seed + a.scenes))
    if a.save_scenes:
        os.makedirs(a.save_scenes, exist_ok=True)
        for s in seeds:
            sc = make_scene(s)
            for way in WAYS:
                text, img = WAYS[way](sc)
                base = os.path.join(a.save_scenes, f"scene{s}_{way}")
                if img:
                    with open(base + ".png", "wb") as f: f.write(img)
                else:
                    with open(base + ".txt", "w", encoding="utf-8") as f: f.write(text)
            with open(os.path.join(a.save_scenes, f"scene{s}_questions.txt"), "w", encoding="utf-8") as f:
                f.write("\n\n".join(f"{q['text']}\nright answer: {q['answer']}" for q in sc["questions"]))
        print(f"wrote {len(seeds)} scenes to {a.save_scenes}")
        if not a.model: return
    if not a.model: p.error("give --model (or use --selftest / --save-scenes)")
    ways = [w.strip() for w in a.ways.split(",") if w.strip() in WAYS]
    if a.text_only: ways = [w for w in ways if w in ("grid", "words")]
    print(f"Experiment 001: {a.model}, {len(seeds)} scenes, ways: {', '.join(ways)}")
    results = run(make_model(a.model, a.provider, a.url, a.key_env), seeds, ways)
    print("\n" + table(results))
    with open(a.out, "w") as f:
        json.dump(dict(model=a.model, provider=a.provider, seeds=seeds, ways=ways, results=results), f, indent=1)
    print(f"\nsaved every answer to {a.out}")


if __name__ == "__main__":
    main()
