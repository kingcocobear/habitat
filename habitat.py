"""
HABITAT - a free, offline world where beings live in places, remember, learn,
and have 3-parent children. No dependencies (pure Python + built-in tkinter).

Run the window :  python habitat.py
Run without GUI :  python habitat.py --headless 20000 --seed 1
Save / resume   :  python habitat.py --save world.json     (saves on close + every 2000 ticks)
                   python habitat.py --load world.json --save world.json

In the window: click a being to inspect it. Buttons: pause / faster / slower.

Everyone carries a notebook and pencil. They draw what they see, build and play
instruments, gather materials, and the bold ones set out from the Wilds to explore
the generated universe in cosmos.py (keep both files in the same folder; without
cosmos.py the habitat still runs, just with no expeditions).

Every being "thinks" on its own timer (the idle-thought loop). The thinking
here is rule-based, so it costs nothing. To give some beings a real language
model later, set LLM_HOOK to a function (see bottom of think()).
"""
import math, random, argparse, json, os, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import cosmos as COSMOS          # the procedurally generated universe (optional)
except ImportError:
    COSMOS = None
try:
    import gallery as GALLERY        # turns the beings' art and songs into a web page for humans (optional)
except ImportError:
    GALLERY = None

TRAITS = ["curiosity", "sociability", "caution", "energy", "creativity"]
SKILLS = ["physics", "chemistry", "planning", "engineering", "storytelling", "exploration", "drawing", "music"]
VALUES = ["truth-seeking", "connection", "progress", "safety", "creativity", "harmony"]
CORE_VALUES = {"safety"}            # always passed down if any parent has it

YEAR = 100                          # ticks per "year"
ADULT, LIFE, CAP = 16 * YEAR, 65 * YEAR, 60
WILDS_FINDS = ["a hidden spring", "strange footprints", "an old wreck", "a field of glowing moss",
               "a cave with carvings", "a ring of standing stones"]
WORKSHOP_ITEMS = ["a lantern", "a better tool", "a small engine", "a map frame", "a kite", "a water filter"]
INSTRUMENTS = ["flute", "drum", "lyre", "music box", "whistle"]
PAGES, PENCIL_LIFE = 40, 25          # a fresh notebook has 40 pages; a pencil lasts 25 sketches
EXP_RATE = 6                         # an expedition makes one jump every 6 ticks
MAX_AWAY = .22                       # at most this share of the population is off exploring
SKETCH = {
    "The Shore": ["the tide line", "a gull on the rocks", "the far horizon", "driftwood"],
    "The Wilds": ["a hidden hollow", "tall strange trees", "animal tracks", "a rock arch"],
    "Observatory": ["the night sky", "the great lens", "a falling star", "the moon"],
    "The Grove": ["an old tree", "dappled light", "a sleeping friend", "mushrooms"],
    "Glass Gardens": ["a glass flower", "light through leaves", "a curling vine"],
    "Quiet Plaza": ["people talking", "the fountain", "long evening shadows"],
}
TASTE = {                              # which two traits make a being love a kind of picture
    "The Shore": ("sociability", "caution"), "The Grove": ("caution", "creativity"),
    "Glass Gardens": ("creativity", "caution"), "Observatory": ("curiosity", "creativity"),
    "The Wilds": ("curiosity", "energy"), "Quiet Plaza": ("sociability", "energy"),
    "among the stars": ("curiosity", "energy"),
}
SONG_KINDS = ["tune", "song", "lullaby", "dance", "march"]
SONG_MOODS = ["gentle", "bright", "slow", "restless", "happy", "wistful"]
SONG_ABOUT = ["the Shore", "the Wilds", "the stars", "the Hearth", "an old friend", "the first rain", "the long walk home"]
LLM_HOOK = None                     # def hook(agent, context) -> str | None

PLACES = {   # cap=capacity, rest/social=effect strength, skill=what grows here
    "The Hearth":    dict(cap=14, rest=1.0, social=1.0, teach=True, music=.6, color="#ffb04f"),
    "Glass Gardens": dict(cap=10, rest=0.6, social=0.4, skill="chemistry", scenic=.7, color="#6fe3b5"),
    "Observatory":   dict(cap=8,  rest=0.3, social=0.2, skill="physics", novel=0.3, scenic=.9, color="#a98bff"),
    "The Shore":     dict(cap=12, rest=0.7, social=0.5, scenic=.8, music=.5, gather=.004, color="#6ec1ff"),
    "Quiet Plaza":   dict(cap=12, rest=0.4, social=0.7, skill="planning", scenic=.3, music=.4, color="#ff8fc0"),
    "The Grove":     dict(cap=10, rest=1.6, social=0.2, scenic=.6, music=.3, gather=.004, color="#8be28b"),
    "The Stage":     dict(cap=16, rest=0.0, social=1.6, skill="storytelling", music=1.0, color="#ffb27a"),
    "Workshop":      dict(cap=8,  rest=0.0, social=0.3, skill="engineering", cost=0.25, novel=0.5, craft=True, color="#c9c9d6"),
    "The Archive":   dict(cap=8,  rest=0.2, social=0.1, archive=True, novel=0.3, color="#e8d27a"),
    "The Nursery":   dict(cap=12, rest=0.6, social=0.6, teach=True, color="#ffc9e0"),
    "The Gallery":   dict(cap=12, rest=0.3, social=0.9, art=True, novel=0.4, color="#d9c7ff"),
    "The Wilds":     dict(cap=10, rest=0.0, social=0.2, skill="exploration", cost=0.3, risk=0.1, novel=0.6, finds=True, scenic=1.0, gather=.012, launch=True, color="#9aa36a"),
}

def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))

def dirichlet(n):
    g = [random.gammavariate(1, 1) for _ in range(n)]
    s = sum(g); return [x / s for x in g]

class Agent:
    def __init__(s, name, traits, skills, values, age, own_memories=None,
                 inherited=None, parents=(), weights=(), gen=0):
        s.name, s.traits, s.skills, s.values = name, traits, skills, values
        s.age, s.parents, s.weights, s.gen = age, list(parents), list(weights), gen
        s.memories = own_memories or []      # (tick, text) - lived experience
        s.inherited = inherited or []        # "[from X] ..." - ancestral knowledge
        s.life = LIFE + random.randint(-5 * YEAR, 5 * YEAR)
        s.energy, s.lonely, s.cool, s.next_think = 80.0, 30.0, 0, 0
        s.bored, s.fame, s.items = 0.0, 0.0, 0
        s.pages, s.pencil = PAGES, PENCIL_LIFE          # everyone starts with a notebook and a pencil
        s.instruments, s.songs, s.wonders_seen = [], [], []
        s.mats, s.sketches, s.books, s.engaged = 0.0, 0, 0, 0
        s.expedition = None                              # a cosmos Explorer while away among the stars
        s.place, s.sx, s.sy = None, None, None

    def dominant(s): return max(s.traits, key=s.traits.get)

SAVE_VERSION = 1
AGENT_FIELDS = ["name", "traits", "skills", "values", "age", "parents", "weights", "gen", "life",
                "energy", "lonely", "cool", "next_think", "place", "inherited", "bored", "fame", "items",
                "pages", "pencil", "instruments", "songs", "mats", "sketches", "books", "engaged", "wonders_seen"]

def chart_pts(e, limit=80):
    pts = sorted(list(p) for p in e.visited)
    if len(pts) > limit:
        step = len(pts) / limit; pts = [pts[int(i * step)] for i in range(limit)]
    for w in e.wonders:                      # the wonders must be on the chart, so others can find them
        if w[0] not in pts: pts.append(list(w[0]))
    return pts

def exp_to_dict(e):
    v, st, g = e.r.getstate()
    return {"name": e.name, "t": e.t, "skill": e.skill, "pos": list(e.pos), "fuel": e.fuel,
            "supplies": e.supplies, "health": e.health, "cargo": e.cargo, "store": e.store,
            "visited": sorted(list(p) for p in e.visited), "log": e.log[-30:],
            "discoveries": e.discoveries, "alive": e.alive, "cause": e.cause, "jumps": e.jumps,
            "landings": e.landings, "trips": e.trips, "far": e.far, "steps": e.steps,
            "wonders": e.wonders, "goal": list(e.goal) if e.goal else None,
            "route": sorted(list(p) for p in e.route), "reached": e.reached,
            "homebound": e.homebound, "meta": e.meta, "rng": [v, list(st), g]}

def exp_from_dict(d):
    e = COSMOS.Explorer(d["name"], d["t"], random.Random())
    e.skill, e.pos, e.fuel, e.supplies, e.health = d["skill"], tuple(d["pos"]), d["fuel"], d["supplies"], d["health"]
    e.cargo, e.store, e.visited = d["cargo"], d["store"], {tuple(p) for p in d["visited"]}
    e.log, e.discoveries, e.alive, e.cause = d["log"], d["discoveries"], d["alive"], d["cause"]
    e.jumps, e.landings, e.trips, e.far, e.steps = d["jumps"], d["landings"], d["trips"], d["far"], d["steps"]
    e.wonders, e.goal = d.get("wonders", []), tuple(d["goal"]) if d.get("goal") else None
    e.route, e.reached = {tuple(p) for p in d.get("route", [])}, d.get("reached", False)
    e.homebound, e.meta = d.get("homebound", False), d.get("meta", {})
    v, st, g = d["rng"]; e.r.setstate((v, tuple(st), g))
    return e

def agent_to_dict(a):
    d = {k: getattr(a, k) for k in AGENT_FIELDS}
    d["memories"] = [list(m) for m in a.memories]
    d["expedition"] = exp_to_dict(a.expedition) if a.expedition else None
    return d

def agent_from_dict(d):
    a = Agent(d["name"], d["traits"], d["skills"], d["values"], d["age"],
              own_memories=[tuple(m) for m in d["memories"]], inherited=d["inherited"],
              parents=d["parents"], weights=d["weights"], gen=d["gen"])
    for k in ("life", "energy", "lonely", "cool", "next_think"): setattr(a, k, d[k])
    for k in ("bored", "fame", "items", "pages", "pencil", "mats", "sketches", "books", "engaged"):
        if k in d: setattr(a, k, d[k])              # older / web saves lack these; the defaults are a starter kit
    a.instruments, a.songs = list(d.get("instruments", [])), list(d.get("songs", []))
    a.wonders_seen = list(d.get("wonders_seen", []))
    if d.get("expedition") and COSMOS: a.expedition = exp_from_dict(d["expedition"])
    a.place = d["place"] if d["place"] in PLACES else random.choice(list(PLACES))
    return a

class World:
    def __init__(s, seed=None, n=12):
        if seed is not None: random.seed(seed)
        s.t, s.agents, s.names, s.archive = 0, [], set(), []
        s.births = s.deaths = 0
        s.cosmos_seed = random.randint(1, 10 ** 6)
        s.cosmos = COSMOS.Cosmos(s.cosmos_seed) if COSMOS else None
        s.gallery, s.songbook, s.art_n = [], {}, 0          # works on the gallery wall, songs beings have composed
        for _ in range(n):
            a = Agent(s.new_name(), {t: round(random.random(), 2) for t in TRAITS},
                      {k: round(random.random() * 0.6, 2) for k in random.sample(SKILLS, 2)},
                      {k: round(random.uniform(.3, 1), 2) for k in random.sample(VALUES, 3)},
                      random.randint(ADULT, ADULT + 20 * YEAR))
            a.place = random.choice(list(PLACES)); a.mats = float(random.randint(0, 2)); s.agents.append(a)

    def new_name(s):
        while True:
            o, v = "kmnrstvzld", "aeiou"
            n = "".join(random.choice(o) + random.choice(v) for _ in range(random.choice([1, 2])))
            n = (n + random.choice(["", "", "n", "r", "x", "l"])).capitalize()
            if n not in s.names: s.names.add(n); return n

    # ---------- save / load (everything is plain JSON text) ----------
    def to_dict(s):
        v, st, g = random.getstate()
        return {"version": SAVE_VERSION, "t": s.t, "births": s.births, "deaths": s.deaths,
                "cosmos_seed": s.cosmos_seed, "gallery": s.gallery, "songbook": s.songbook, "art_n": s.art_n, "names": sorted(s.names), "archive": [list(x) for x in s.archive],
                "agents": [agent_to_dict(a) for a in s.agents], "rng": [v, list(st), g]}

    def save(s, path):
        tmp = path + ".tmp"                      # write first, then swap, so a crash can't corrupt the save
        with open(tmp, "w", encoding="utf-8") as f: json.dump(s.to_dict(), f)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f: d = json.load(f)
        if d.get("version") != SAVE_VERSION:
            raise ValueError(f"save file is version {d.get('version')}, this program reads version {SAVE_VERSION}")
        w = cls.__new__(cls)
        w.t, w.births, w.deaths = d["t"], d["births"], d["deaths"]
        w.names = set(d["names"]); w.archive = [tuple(x) for x in d["archive"]]
        w.cosmos_seed = d.get("cosmos_seed", 1)
        w.cosmos = COSMOS.Cosmos(w.cosmos_seed) if COSMOS else None
        w.gallery, w.songbook = d.get("gallery", []), d.get("songbook", {})
        w.art_n = d.get("art_n", len(w.gallery))
        w.agents = [agent_from_dict(x) for x in d["agents"]]
        w.names.update(a.name for a in w.agents)
        if "rng" in d: v, st, g = d["rng"]; random.setstate((v, tuple(st), g))
        return w

    def remember(s, a, text):
        a.memories.append((s.t, text)); del a.memories[:-25]

    # ---------- reproduction (3 parents) ----------
    def make_child(s, parents, mut=0.12, size=0.06):
        w = dirichlet(len(parents))
        traits = {}
        for t in TRAITS:
            v = sum(wi * p.traits[t] for wi, p in zip(w, parents))
            if random.random() < mut: v += random.gauss(0, size)
            traits[t] = round(clamp(v), 2)
        skills = {}                          # talent: half of what a parent could do
        for k in {k for p in parents for k in p.skills}:
            blend = sum(wi * p.skills.get(k, 0) for wi, p in zip(w, parents))
            best = max(p.skills.get(k, 0) for p in parents)
            prof = 0.4 * blend + 0.6 * best
            if random.random() < min(.95, prof + .3):
                if random.random() < mut: prof += random.gauss(0, size)
                skills[k] = round(clamp(prof) * 0.5, 2)
        values = {}
        for k in {k for p in parents for k in p.values}:
            v = sum(wi * p.values.get(k, 0) for wi, p in zip(w, parents))
            if k in CORE_VALUES and v > 0: v = max(v, 0.3)     # core values never dilute away
            if v > 0.12:
                if random.random() < mut: v += random.gauss(0, size)
                values[k] = round(clamp(v), 2)
        inh = []
        for wi, p in zip(w, parents):
            pool = p.inherited + [f"[from {p.name}] {txt}" for _, txt in p.memories if not txt.startswith("read")]
            if pool: inh += random.sample(pool, min(max(1, round(wi * 4)), len(pool)))
        inh = list(dict.fromkeys(inh))[:8]
        if inh and random.random() < mut:
            i = random.randrange(len(inh))
            inh[i] = inh[i].replace(" (mutated)", "") + " (mutated)"   # never stacks
        gen = max(p.gen for p in parents) + 1
        return Agent(s.new_name(), traits, skills, values, 0, inherited=inh,
                     parents=[p.name for p in parents], weights=[round(x, 2) for x in w], gen=gen)

    def reproduce(s, occ):
        for pn, lst in occ.items():
            if len(s.agents) >= CAP: return
            adults = [a for a in lst if a.age >= ADULT and a.cool == 0 and a.energy > 40 and a.age < a.life * .85]
            if len(adults) >= 2 and random.random() < (.25 if len(adults) >= 3 else .12):
                ps = random.sample(adults, min(3, len(adults)))
                c = s.make_child(ps); c.place = pn
                for p in ps:
                    p.cool = 900; s.remember(p, f"welcomed {c.name} into the world")
                s.agents.append(c); s.births += 1

    # ---------- art, music, crafting, expeditions ----------
    def by_name(s, name):
        return next((x for x in s.agents if x.name == name), None)

    def hang(s, a, kind, title, place, q, **extra):
        s.art_n += 1
        piece = dict(id=s.art_n, kind=kind, artist=a.name, gen=a.gen, age=a.age // YEAR, year=s.t // YEAR,
                     place=place, title=title, seed=random.randint(1, 10 ** 9), accent=COL[a.dominant()],
                     skill=round(a.skills.get("drawing", 0), 2), creativity=round(a.traits["creativity"], 2),
                     q=round(q, 2), admired=0)
        piece.update(extra)
        if kind == "sketch":                              # each artist keeps their best 8 on the wall
            mine = [x for x in s.gallery if x["artist"] == a.name and x["kind"] == "sketch"]
            if len(mine) >= 8:
                worst = min(mine, key=lambda x: x["q"])
                if worst["q"] >= q: return None
                s.gallery.remove(worst)
        s.gallery.append(piece)
        if len(s.gallery) > 240:
            s.gallery.remove(min(s.gallery, key=lambda x: x["q"] + (2 if x["kind"] == "chart" else 0)))
        return piece

    def sketch(s, a, pn, what=None, inspired=None, bonus=0.0):
        what = what or random.choice(SKETCH.get(pn, ["a quiet corner"]))
        ds = a.skills.get("drawing", 0)
        a.pages -= 1; a.pencil -= 1; a.sketches += 1; a.engaged = 60
        a.skills["drawing"] = round(min(1, ds + .004 * (.5 + a.traits["creativity"])), 4)
        a.fame += .05
        q = .5 * ds + .3 * a.traits["creativity"] + .25 * random.random() + bonus
        extra = {"inspired_by": inspired} if inspired else {}
        if q > .34 and s.hang(a, "sketch", what, pn, q, **extra):
            if random.random() < .5:
                s.remember(a, f"drew {what}" + (f", inspired by {inspired['artist']}'s work" if inspired else f" at {pn}") + "; it hangs in the gallery")
        elif random.random() < .15: s.remember(a, f"sketched {what} at {pn}")
        if a.pages <= 0:
            a.books += 1; s.remember(a, "filled a whole sketchbook")
            s.archive.append((a.name, f"filled a sketchbook; the last page shows {what}")); del s.archive[:-200]

    def new_song(s, a, title, inst, inspired=None):
        a.songs = (a.songs + [title])[-6:]
        info = dict(composer=a.name, year=s.t // YEAR, inst=inst, heard=1,
                    seed=random.randint(1, 10 ** 9), accent=COL[a.dominant()])
        if inspired: info["inspired_by"] = inspired
        s.songbook[title] = info
        if len(s.songbook) > 150: del s.songbook[min(s.songbook, key=lambda k: s.songbook[k]["heard"])]

    def perform(s, a, others):
        inst = random.choice(a.instruments); a.engaged = 80
        a.skills["music"] = round(min(1, a.skills.get("music", 0) + .004), 4)
        if not a.songs or random.random() < .1:
            title = (f"a {random.choice(SONG_MOODS)} {random.choice(SONG_KINDS)} "
                     f"about {random.choice(SONG_ABOUT)} ({a.name})")
            s.new_song(a, title, inst); s.remember(a, f"composed {title.split(' (')[0]}")
        else:
            title = random.choice(a.songs)
        short = title.split(" (")[0]
        audience = [o for o in others if o is not a]
        for o in audience:
            o.lonely = clamp(o.lonely - 5, 0, 100)
            if title not in o.songs and random.random() < .12:
                o.songs = (o.songs + [title])[-6:]
                if title in s.songbook: s.songbook[title]["heard"] += 1
                s.remember(o, f"learned {short} from {a.name}")
            if o.instruments and o.traits["creativity"] > .5 and random.random() < .02:      # answer with a tune of their own
                t2 = f"an answer to {short} ({o.name})"
                if t2 not in s.songbook:
                    s.new_song(o, t2, random.choice(o.instruments), inspired={"artist": a.name, "title": short})
                    s.remember(o, f"answered {short} with a tune of their own")
                    s.remember(a, f"{o.name} answered my {short} with a tune of their own"); a.fame += .1
        if audience:
            a.fame += .08 * math.sqrt(len(audience))
            if random.random() < .12: s.remember(a, f"played the {inst} for {len(audience)} listeners")

    def craft(s, a):
        a.mats -= 1
        if a.pencil <= 0: a.pencil = PENCIL_LIFE; what = "a new pencil"
        elif a.pages <= 0: a.pages = PAGES; what = "a fresh notebook"
        elif len(a.instruments) < 3 and (not a.instruments or random.random() < .3):
            ins = random.choice([i for i in INSTRUMENTS if i not in a.instruments])
            a.instruments.append(ins); a.fame += .5; what = f"a {ins}"
        else:
            what = random.choice(WORKSHOP_ITEMS); a.items += 1; a.fame += .7
        s.remember(a, f"made {what} in the Workshop")

    def launch(s, a):
        e = COSMOS.Explorer(a.name, dict(a.traits), random.Random(random.randint(1, 10 ** 9)))
        e.skill = max(e.skill, round(a.skills.get("exploration", 0), 2)); e.steps = 0
        a.expedition = e
        s.remember(a, "set out from the Wilds to explore the stars")

    def fly(s, a, gone):
        e = a.expedition
        if s.t % EXP_RATE: return
        e.step(s.cosmos); e.steps += 1
        if not e.alive: gone.append(a)
        elif e.trips >= 1: s.land_home(a)

    def note(s, pc, text):
        pc.setdefault("notes", []).append(text); del pc["notes"][:-3]

    def react(s, a):
        """A being looks at a work on the wall and reacts according to taste."""
        pc = random.choice(s.gallery[-60:] + random.sample(s.gallery, min(10, len(s.gallery))))
        if pc["artist"] == a.name: return
        t = a.traits; k1, k2 = TASTE.get(pc["place"], ("curiosity", "creativity"))
        ap = .35 * t[k1] + .25 * t[k2] + .4 * pc["q"] + .25 * random.random()
        owner, who, title = s.by_name(pc["artist"]), pc["artist"], pc["title"]
        if ap > .72:
            pc["admired"] += 1; a.lonely = clamp(a.lonely - 3, 0, 100)
            if owner: owner.fame += .12
            if random.random() < .4: s.remember(a, f"was moved by '{title}' by {who}")
            if owner and random.random() < .3: s.remember(owner, f"{a.name} lingered over my '{title}'")
            if random.random() < .5:
                s.note(pc, f"{a.name} " + random.choice(["lingered here a long while", "came back to this one twice", "went quiet in front of it"]))
            if pc["kind"] == "sketch" and a.pages > 0 and a.pencil > 0 and a.age >= 4 * YEAR and t["creativity"] > .4 and random.random() < .3:
                pc["inspired"] = pc.get("inspired", 0) + 1
                s.note(pc, f"{a.name} went off to draw one of their own")
                s.sketch(a, pc["place"], title, inspired={"artist": who, "title": title, "kind": "sketch"}, bonus=.08)
                a.skills["drawing"] = round(min(1, a.skills.get("drawing", 0) + .006), 4)
            elif pc["kind"] == "chart":
                s.consider_pilgrimage(a, pc)
        elif ap < .24 and a.skills.get("drawing", 0) > .45 and t["sociability"] > .4 and owner and random.random() < .25:
            owner.skills["drawing"] = round(min(1, owner.skills.get("drawing", 0) + .01), 4)
            s.remember(owner, f"{a.name} shared a tip about shading with me"); s.remember(a, f"gave {who} a tip on '{title}'")
            s.note(pc, f"{a.name} offered a tip on shading")

    def consider_pilgrimage(s, a, pc):
        """A star chart marks wonders. A curious being may decide to go and see one."""
        if not (s.cosmos and pc.get("wonders")) or a.expedition: return
        t = a.traits
        if not (a.age >= ADULT and a.age < a.life * .6 and a.items >= 1 and a.energy > 35 and t["curiosity"] > .45): return
        if sum(1 for x in s.agents if x.expedition) >= MAX_AWAY * len(s.agents): return
        options = [w for w in pc["wonders"] if w[1] not in a.wonders_seen and math.dist(w[0], (0, 0, 0)) < 27]
        if not options or random.random() > .35 * (1 - .6 * t["caution"]) * (.4 + t["curiosity"]): return
        coords, text = random.choice(options)
        e = COSMOS.Explorer(a.name, dict(a.traits), random.Random(random.randint(1, 10 ** 9)))
        e.skill = max(e.skill, round(a.skills.get("exploration", 0), 2)); e.steps = 0
        e.goal, e.route = tuple(coords), {tuple(q) for q in pc.get("pts", [])}
        e.meta = {"piece": pc["id"], "text": text, "artist": pc["artist"]}
        a.expedition = e
        clean = text.split(" on ")[0]
        s.remember(a, f"studied {pc['artist']}'s star chart and set out to see {clean}")
        s.note(pc, f"{a.name} set out to see {clean}")

    def land_home(s, a):
        e, a.expedition = a.expedition, None
        n, ds = len(e.visited), e.discoveries
        a.mats = min(8.0, a.mats + min(5, sum(e.store.values()) / 10))
        a.skills["exploration"] = round(min(1, max(a.skills.get("exploration", 0), e.skill)), 3)
        a.energy, a.bored = 45.0, 0.0
        if e.meta.get("piece"):                                   # came back from a pilgrimage along someone's chart
            clean, who = e.meta["text"].split(" on ")[0], e.meta["artist"]
            pc = next((x for x in s.gallery if x["id"] == e.meta["piece"]), None)
            if e.reached:
                a.fame += .8; a.wonders_seen = (a.wonders_seen + [e.meta["text"]])[-12:]
                s.remember(a, f"stood before {clean}, just as {who}'s chart promised")
                owner = s.by_name(who)
                if owner: owner.fame += .6; s.remember(owner, f"{a.name} traveled to {clean} using my chart")
                if pc:
                    pc["pilgrims"] = (pc.get("pilgrims", []) + [a.name])[-6:]; s.note(pc, f"{a.name} traveled here and saw {clean}")
                if a.pages > 0 and a.pencil > 0:
                    s.sketch(a, "among the stars", clean, bonus=.12,
                             inspired={"artist": who, "title": pc["title"] if pc else "a star chart", "kind": "chart"})
            else:
                s.remember(a, f"turned back before reaching {clean}")
            return
        a.fame += .6 + .5 * math.sqrt(len(ds))
        s.remember(a, f"came home from the stars after charting {n} systems")
        for d in ds[:3]: s.archive.append((a.name, f"discovered {d} among the stars"))
        s.archive.append((a.name, f"star log: charted {n} systems, as far as {e.far:.0f} cells from home"))
        del s.archive[:-200]
        if n >= 8:
            s.hang(a, "chart", f"star chart: {n} systems", "among the stars", 1.0, pts=chart_pts(e), found=len(ds),
                   wonders=e.wonders[:8], pilgrims=[])

    def export_gallery(s, path):
        if not GALLERY: raise RuntimeError("gallery.py was not found next to habitat.py")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: f.write(GALLERY.render(s))
        os.replace(tmp, path)
        return len(s.gallery), len(s.songbook)

    # ---------- thinking: where do I want to be? ----------
    def score(s, a, pn, P, occ):
        n = len(occ[pn]) - (pn == a.place)
        if n >= P["cap"] or (P.get("art") and not s.gallery): return -99
        t = a.traits
        sc = (100 - a.energy) / 100 * P["rest"] * 2.5 + a.lonely / 100 * P["social"] * 2
        sc += t["sociability"] * P["social"] * .8
        if P.get("skill"):
            sc += .6 * t["curiosity"] + .4 * a.skills.get(P["skill"], 0)
            if P.get("cost"): sc -= (1 - t["energy"]) * .6
        risk = P.get("risk", 0)
        sc += t["curiosity"] * risk * 4 * (1 - t["caution"]) - t["caution"] * risk * 5
        if P.get("craft"): sc += .6 * t["creativity"] + .4 * a.skills.get("engineering", 0) + .15 * a.items
        if P.get("archive"): sc += .4 * t["creativity"] + .3 * t["curiosity"]
        if P.get("art"):                                             # the gallery is worth a visit when there is something on the wall
            sc += .4 * t["creativity"] + .4 * t["curiosity"] + .15 * t["sociability"] + .25 * min(4, sum(1 for x in s.gallery if x["artist"] == a.name))
        if pn == "The Stage": sc += .5 * t["creativity"]
        if P.get("scenic") and a.pages > 0 and a.pencil > 0:        # a notebook makes beautiful places worth visiting
            sc += P["scenic"] * (.2 + .7 * t["creativity"]) * (1 + a.skills.get("drawing", 0))
        if P.get("music") and a.instruments:
            sc += P["music"] * (.2 + .7 * t["creativity"]) * (1 + a.skills.get("music", 0))
        if P.get("craft") and a.mats >= 1 and (a.pencil <= 0 or a.pages <= 0 or not a.instruments):
            sc += 1.6                                                # I have materials and need something made
        if P.get("gather") and a.mats < 1 and (a.pencil <= 3 or a.pages <= 3 or not a.instruments):
            sc += .6 + P["gather"] * 40 * (1 - .6 * t["caution"])    # I need materials
        if a.age < ADULT:
            sc += 2.5 if P.get("teach") else 0
            sc -= 8 * risk * 10
        sc += a.bored / 100 * P.get("novel", 0) * 3 * (.3 + t["curiosity"]) * (1 - .6 * t["caution"])   # bold, curious beings crave somewhere new
        if pn == a.place: sc -= a.bored / 100 * 1.2
        sc += .25 * t["sociability"] * sum(o.fame for o in occ[pn] if o is not a) ** .5   # crowds follow success
        if a.age >= ADULT and a.cool == 0:            # ready adults seek each other out
            sc += .5 * sum(1 for o in occ[pn] if o is not a and o.age >= ADULT and o.cool == 0) ** .5
        sc -= 1.5 * max(0, (n + 1) / P["cap"] - .6)
        return sc + (.4 if pn == a.place else 0) + (1.2 if pn == a.place and a.engaged > 0 else 0)

    def think(s, a, occ):
        a.next_think = s.t + random.randint(20, 60)
        sc = {pn: s.score(a, pn, P, occ) for pn, P in PLACES.items()}
        if a.energy < 12: sc = {pn: PLACES[pn]["rest"] - (sc[pn] < -50) * 9 for pn in sc}
        w = [math.exp(min(v, 8) / .5) for v in sc.values()]
        new = random.choices(list(sc), w)[0]
        if new != a.place and random.random() < .08: s.remember(a, f"went to {new}")
        a.place = new
        if LLM_HOOK and random.random() < .02:      # optional paid thinking
            txt = LLM_HOOK(a, {"place": a.place, "memories": a.memories[-5:]})
            if txt: s.remember(a, txt)

    # ---------- life in a place ----------
    def live(s, a, occ):
        P = PLACES[a.place]; others = occ[a.place]; n = len(others) - 1
        cost = P.get("cost", 0) * (1 - min(.5, .1 * a.items))        # tools make hard work easier
        a.energy = clamp(a.energy + P["rest"] * .35 - .12 - cost, 0, 100)
        a.bored = clamp(a.bored + .08 * (.5 + a.traits["curiosity"]) - P.get("novel", 0) * .30, 0, 100)
        a.fame = max(0.0, a.fame - .0005)
        if a.engaged > 0: a.engaged -= 1
        if P.get("finds") and a.age >= ADULT and random.random() < .004 * (.5 + a.traits["curiosity"]) * (.5 + a.skills.get("exploration", 0)):
            f = random.choice(WILDS_FINDS); a.fame += 1.0; s.remember(a, f"found {f} in the Wilds")
            if random.random() < .5: s.archive.append((a.name, f"found {f} in the Wilds")); del s.archive[:-200]
            if a.pages > 0 and a.pencil > 0 and random.random() < .6: s.sketch(a, a.place, f)    # a find is worth drawing
        if P.get("gather") and a.age >= 8 * YEAR and a.mats < 8 and random.random() < P["gather"] * (.4 + a.traits["energy"]):
            a.mats += 1.0
        if P.get("craft") and a.age >= ADULT and a.mats >= 1 and random.random() < .02 * (.5 + a.skills.get("engineering", 0)):
            s.craft(a)
        if P.get("scenic") and a.age >= 4 * YEAR and a.pages > 0 and a.pencil > 0 and \
                random.random() < .007 * P["scenic"] * (.3 + a.traits["creativity"]) * (.6 + a.skills.get("drawing", 0)):
            s.sketch(a, a.place)
        if P.get("music") and a.instruments and a.age >= 6 * YEAR and \
                random.random() < .005 * P["music"] * (.3 + a.traits["creativity"]) * (.6 + a.skills.get("music", 0)):
            s.perform(a, others)
        if P.get("launch") and s.cosmos and a.age >= ADULT and a.age < a.life * .6 and a.items >= 1 and a.energy > 55 \
                and a.traits["curiosity"] > .5 and random.random() < .02 * (1 - a.traits["caution"]) * (.5 + a.skills.get("exploration", 0)) \
                and sum(1 for x in s.agents if x.expedition) < MAX_AWAY * len(s.agents):
            s.launch(a)
        if P.get("art") and s.gallery and random.random() < .02: s.react(a)      # look at the work on the wall
        a.lonely = clamp(a.lonely + .08 - P["social"] * .3 * min(1, n / 3), 0, 100)
        k = P.get("skill")
        if k:
            rate = 1.5 if a.age < ADULT else 1
            a.skills[k] = round(min(1, a.skills.get(k, 0) + .0006 * (.5 + a.traits["curiosity"]) * rate), 4)
        if P.get("teach") and a.age < ADULT:
            teachers = [o for o in others if o.age >= ADULT and o.skills]
            if teachers:
                tk = max(random.choice(teachers).skills.items(), key=lambda kv: kv[1])[0]
                a.skills[tk] = round(min(1, a.skills.get(tk, 0) + .0015), 4)
        if P.get("risk") and random.random() < P["risk"] * .01:
            a.energy = max(0, a.energy - 15); s.remember(a, "survived a scare in the Wilds")
        if P.get("archive") and random.random() < .01:
            mine = [x for _, x in a.memories if not x.startswith("read")]
            if mine and random.random() < .5: s.archive.append((a.name, random.choice(mine)))
            else:
                notes = [x for x in s.archive if x[0] != a.name]
                if notes: who, txt = random.choice(notes); s.remember(a, f"read in the Archive: {txt[:70]}")
            del s.archive[:-200]
        if n >= 1 and random.random() < .004:
            s.remember(a, f"met {random.choice([o for o in others if o is not a]).name} at {a.place}")

    def die(s, a):
        e = a.expedition
        if e and not e.alive:
            s.archive.append((a.name, f"lost among the stars ({e.cause}) after charting {len(e.visited)} systems"))
            for d in e.discoveries[:2]: s.archive.append((a.name, f"last transmission: discovered {d}"))
            if len(e.visited) >= 8 and not e.meta.get("piece"):
                s.hang(a, "chart", "the last star chart", "among the stars", 1.0, pts=chart_pts(e),
                       found=len(e.discoveries), wonders=e.wonders[:8], pilgrims=[])
        else:
            top = max(a.values, key=a.values.get) if a.values else "life"
            s.archive.append((a.name, f"legacy of {a.name}: lived {a.age // YEAR} years, held {top} dear"))
        del s.archive[:-200]
        a.expedition = None
        s.deaths += 1

    def tick(s):
        s.t += 1
        occ = {p: [] for p in PLACES}
        for a in s.agents:
            if not a.expedition: occ[a.place].append(a)
        gone = []
        for a in s.agents:
            a.age += 1; a.cool = max(0, a.cool - 1)
            if a.age >= a.life: gone.append(a); continue
            if a.expedition: s.fly(a, gone); continue          # away among the stars
            s.live(a, occ)
            if s.t >= a.next_think or a.energy < 12: s.think(a, occ)
        for a in gone: s.die(a); s.agents.remove(a)
        if s.t % 25 == 0: s.reproduce(occ)

    def summary(s):
        by = {p: 0 for p in PLACES}
        away = 0
        for a in s.agents:
            if a.expedition: away += 1
            else: by[a.place] += 1
        return (f"t={s.t:6d} pop={len(s.agents):3d} gen={max([a.gen for a in s.agents], default=0)} "
                f"births={s.births} deaths={s.deaths} archive={len(s.archive)} art={len(s.gallery)} songs={len(s.songbook)}\n   " +
                " ".join(f"{p.split()[-1]}:{c}" for p, c in by.items()) + f" Away:{away}")

# ================= window =================
COL = dict(curiosity="#6ec1ff", sociability="#ff8fc0", caution="#8be28b", energy="#ffb04f", creativity="#a98bff")

# ---------------------------------------------------------------- little pixel people (original, drawn from code)
SKIN = ["#ffdcb8", "#f1c27d", "#d9a066", "#b5764a", "#8d5524", "#6b3f1f"]
HAIR = ["#2b1d14", "#5a3825", "#8a5a2b", "#d9a441", "#b0452b", "#3c3c4a", "#e8e0d0", "#4a6fa5", "#7a4fa0"]
OUT = "#1a1424"

def shade(hexc, f):
    c = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * f))) for v in c)

def sprite_look(a):
    """Each being keeps the same face, hair and skin for life: a stable look made from its name (and its parents' look can't change it)."""
    r = random.Random(sum(ord(ch) * (i + 7) for i, ch in enumerate(a.name)))
    return dict(skin=r.choice(SKIN), hair=r.choice(HAIR), style=r.randrange(4), eyes=r.choice(["#1a1a2e", "#2a4d3a", "#3a2a1a", "#244a7a"]),
                pants=r.choice(["#2f3b5c", "#3d2f45", "#394a3a", "#4a3a2a"]))

def sprite_grid(a, frame=0, face=1, child=False, look=None):
    """14 wide x 18 tall grid of colours (None = see-through). frame 0/1 = walking steps, face = 1 right, -1 left."""
    look = look or sprite_look(a); W_, H_ = 14, 18
    g = [[None] * W_ for _ in range(H_)]
    def px(x, y, c):
        if 0 <= x < W_ and 0 <= y < H_: g[y][x] = c
    def rect(x0, y0, x1, y1, c):
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1): px(xx, yy, c)
    shirt = COL[a.dominant()]; skin, hair = look["skin"], look["hair"]
    # legs (swap a step every frame)
    lift = frame % 2
    rect(4, 13, 5, 15 - lift, look["pants"]); rect(8, 13, 9, 14 + lift + 1, look["pants"])
    px(4, 16 - lift, "#2a2030"); px(5, 16 - lift, "#2a2030"); px(8, 15 + lift, "#2a2030"); px(9, 15 + lift, "#2a2030")
    # body + arms
    rect(4, 9, 9, 12, shirt); rect(4, 12, 9, 12, shade(shirt, .78))
    swing = 1 if frame % 2 else 0
    rect(3, 10 + swing, 3, 12 + swing, skin); rect(10, 11 - swing, 10, 13 - swing, skin)
    # head
    rect(4, 3, 9, 8, skin); rect(4, 8, 9, 8, shade(skin, .92))
    e1, e2 = (6, 8) if face > 0 else (5, 7)
    for cx in (e1, e2): px(cx, 6, look["eyes"]); px(cx, 5, "#ffffff")
    px(e1 + 1, 7, shade(skin, .6))                              # tiny mouth
    px(4, 7, "#ff9aa2" if a.age < ADULT else shade(skin, .9)); px(9, 7, "#ff9aa2" if a.age < ADULT else shade(skin, .9))
    # hair
    st = look["style"]
    rect(4, 2, 9, 3, hair); rect(3, 3, 3, 4, hair); rect(10, 3, 10, 4, hair)
    if st == 0: pass                                            # short
    elif st == 1: rect(3, 4, 3, 10, hair); rect(10, 4, 10, 10, hair)   # long
    elif st == 2: rect(5, 1, 5, 1, hair); rect(7, 1, 7, 1, hair); rect(9, 1, 9, 1, hair); rect(4, 1, 9, 2, hair)    # spiky
    elif st == 3: rect(4, 1, 9, 2, shade(shirt, 1.0)); rect(3, 3, 10, 3, shade(shirt, .85)); rect(4, 4, 9, 4, hair)  # cap in their colour
    if st != 3: rect(5, 4, 8, 4, hair) if st != 1 else rect(4, 4, 9, 4, hair)
    if child:                                                   # little ones: shorter body, same big head
        for y in range(10, 12):
            del g[y]; g.insert(0, [None] * W_)
    # outline pass: gives that clean sprite edge
    out = [[g[y][x] for x in range(W_)] for y in range(H_)]
    for y in range(H_):
        for x in range(W_):
            if g[y][x] is None and any(0 <= y + dy < H_ and 0 <= x + dx < W_ and g[y + dy][x + dx]
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = OUT
    return out

def run_gui(world, save_path=None, gallery_path=None):
    import tkinter as tk
    CW, CH, COLS = 780, 640, 4
    cw, ch = CW // COLS, 190
    root = tk.Tk(); root.title("Habitat")
    cv = tk.Canvas(root, width=CW, height=CH, bg="#0c0b14", highlightthickness=0); cv.pack(side="left")
    side = tk.Frame(root, bg="#14121f"); side.pack(side="right", fill="both", expand=True)
    bar = tk.Frame(side, bg="#14121f"); bar.pack(fill="x")
    info = tk.Text(side, width=46, bg="#14121f", fg="#d8d4f0", font=("Consolas", 10), relief="flat", wrap="word")
    info.pack(fill="both", expand=True)
    st = dict(paused=False, speed=2, sel=None, sprites=True); speeds = [1, 2, 5, 10, 25, 60]
    cells = {p: (30 + (i % COLS) * cw, 40 + (i // COLS) * ch) for i, p in enumerate(PLACES)}

    def btn(txt, fn): tk.Button(bar, text=txt, command=fn, bg="#2a2640", fg="white", relief="flat").pack(side="left", padx=3, pady=4)
    sprite_cache = {}
    def make_sprite(a, fr, face, child):
        g = sprite_grid(a, fr, face, child)
        im = tk.PhotoImage(width=len(g[0]), height=len(g))      # new pixels start see-through
        for y, row in enumerate(g):
            for x, c in enumerate(row):
                if c: im.put(c, to=(x, y))
        return im.zoom(2, 2)
    def pause(): st["paused"] = not st["paused"]
    def toggle_sprites(): st["sprites"] = not st["sprites"]
    def faster(): st["speed"] = min(len(speeds) - 1, st["speed"] + 1)
    def slower(): st["speed"] = max(0, st["speed"] - 1)
    path = save_path or "habitat_save.json"
    last = [world.t]
    def save_now():
        world.save(path); last[0] = world.t
        info.insert("end", f"\n\nsaved to {path}")
    gpath = gallery_path or "gallery.html"
    def open_gallery():
        try:
            n, m = world.export_gallery(gpath)
            import webbrowser; webbrowser.open("file://" + os.path.abspath(gpath))
            info.insert("end", f"\n\ngallery: {n} works, {m} songs -> {gpath}")
        except Exception as ex:
            info.insert("end", f"\n\ngallery failed: {ex}")
    def on_close():
        if save_path: world.save(path)
        if gallery_path:
            try: world.export_gallery(gallery_path)
            except Exception: pass
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
    btn("pause", pause); btn("faster", faster); btn("slower", slower); btn("save", save_now); btn("gallery", open_gallery); btn("sprites / dots", toggle_sprites)

    def click(e):
        shown = [a for a in world.agents if a.sx is not None and not a.expedition]
        best = min(shown, key=lambda a: (a.sx - e.x) ** 2 + (a.sy - e.y) ** 2, default=None)
        st["sel"] = best if best and (best.sx - e.x) ** 2 + (best.sy - e.y) ** 2 < 300 else None
    cv.bind("<Button-1>", click)

    def show(a):
        info.delete("1.0", "end")
        if not a or a not in world.agents:
            info.insert("end", world.summary() + "\n\nClick a being to inspect it."); return
        f = lambda d: "\n".join(f"  {k:14s}{v:.2f}" for k, v in sorted(d.items(), key=lambda kv: -kv[1])) or "  -"
        mem = "\n".join(f"  t{t}: {x}" for t, x in a.memories[-6:]) or "  -"
        inh = "\n".join(f"  {x}" for x in a.inherited) or "  -"
        e = a.expedition
        away = (f"AWAY among the stars: {len(e.visited)} systems charted, fuel {e.fuel:.0f}, supplies {e.supplies:.0f}\n"
                if e else "")
        works = sum(1 for x in world.gallery if x["artist"] == a.name)
        info.insert("end", f"{a.name}  (gen {a.gen}, {a.age // YEAR} yrs)\nat {a.place}\n{away}"
                    f"energy {a.energy:.0f}   lonely {a.lonely:.0f}   bored {a.bored:.0f}\n"
                    f"fame {a.fame:.1f}   items built {a.items}\n"
                    f"notebook {a.pages} pages, pencil {a.pencil}, materials {a.mats:.0f}\n"
                    f"instruments: {', '.join(a.instruments) or 'none'}\n"
                    f"sketches {a.sketches}, books filled {a.books}, works in gallery {works}\n"
                    f"songs: {'; '.join(x.split(' (')[0] for x in a.songs) or 'none'}\n"
                    f"wonders seen in person: {len(a.wonders_seen)}\n"
                    f"parents: {', '.join(a.parents) or 'founder'} {a.weights or ''}\n\n"
                    f"TRAITS\n{f(a.traits)}\n\nSKILLS\n{f(a.skills)}\n\nVALUES\n{f(a.values)}\n\n"
                    f"OWN MEMORIES\n{mem}\n\nINHERITED\n{inh}")

    frame = [0]
    def loop():
        if not st["paused"]:
            for _ in range(speeds[st["speed"]]): world.tick()
        if save_path and world.t - last[0] >= 2000: world.save(path); last[0] = world.t
        cv.delete("all")
        for p, (x, y) in cells.items():
            cv.create_rectangle(x, y, x + cw - 20, y + ch - 25, outline=PLACES[p]["color"], width=2, fill="#13111f")
            cv.create_text(x + 8, y + 8, anchor="nw", text=p.upper(), fill=PLACES[p]["color"], font=("Consolas", 8))
        groups = {}
        for a in world.agents:
            if not a.expedition: groups.setdefault(a.place, []).append(a)
        for p, lst in groups.items():
            x, y = cells[p]; cx, cy = x + (cw - 20) / 2, y + (ch - 25) / 2 + 8
            for i, a in enumerate(lst):
                ang = 2 * math.pi * i / len(lst); r = 12 + 7 * math.sqrt(len(lst))
                tx, ty = cx + r * math.cos(ang), cy + r * math.sin(ang) * .7
                if a.sx is None: a.sx, a.sy = tx, ty
                a.sx += (tx - a.sx) * .15; a.sy += (ty - a.sy) * .15
        for a in world.agents:
            if a.expedition: continue
            rad = 4 + 5 * min(1, a.age / ADULT)
            if st["sprites"]:
                moving = abs(a.sx - getattr(a, "_lx", a.sx)) + abs(a.sy - getattr(a, "_ly", a.sy)) > .25
                if abs(a.sx - getattr(a, "_lx", a.sx)) > .2: a._face = 1 if a.sx > a._lx else -1
                a._lx, a._ly = a.sx, a.sy
                fr = (frame[0] // 4) % 2 if moving else 0
                key = (a.name, fr, getattr(a, "_face", 1), a.age < ADULT, a.dominant())
                im = sprite_cache.get(key)
                if im is None:
                    im = make_sprite(a, fr, key[2], key[3]); sprite_cache[key] = im
                if a is st["sel"]:
                    cv.create_oval(a.sx - 11, a.sy + 12, a.sx + 11, a.sy + 20, outline="white")
                else:
                    cv.create_oval(a.sx - 8, a.sy + 13, a.sx + 8, a.sy + 19, fill="#0a0912", outline="")
                cv.create_image(a.sx, a.sy + 2, image=im, anchor="center")
                rad = 17
            else:
                cv.create_oval(a.sx - rad, a.sy - rad, a.sx + rad, a.sy + rad, fill=COL[a.dominant()], outline="white" if a is st["sel"] else "")
            if a is st["sel"] or len(world.agents) < 25:
                cv.create_text(a.sx, a.sy + rad + 6, text=a.name, fill="#aaa", font=("Consolas", 7))
        cv.create_text(10, 12, anchor="w", fill="#8a86a8", font=("Consolas", 9),
                       text=f"year {world.t // YEAR}   pop {len(world.agents)} ({sum(1 for a in world.agents if a.expedition)} away)   art {len(world.gallery)}   x{speeds[st['speed']]}" + ("   PAUSED" if st["paused"] else ""))
        frame[0] += 1
        if frame[0] % 6 == 0: show(st["sel"])
        root.after(40, loop)
    loop(); root.mainloop()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", type=int, default=0, help="run N ticks with no window")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--agents", type=int, default=12)
    ap.add_argument("--save", metavar="FILE", help="save the world here (on exit, and every 2000 ticks in the window)")
    ap.add_argument("--load", metavar="FILE", help="resume a saved world")
    ap.add_argument("--gallery", metavar="FILE", help="write the beings' art gallery as a web page (open it in any browser)")
    args = ap.parse_args()
    try:
        w = World.load(args.load) if args.load else World(args.seed, args.agents)
    except (OSError, ValueError, KeyError) as e:
        raise SystemExit(f"Could not load '{args.load}': {e}")
    if args.headless:
        for i in range(args.headless):
            w.tick()
            if (i + 1) % (args.headless // 5 or 1) == 0: print(w.summary())
        if args.save: w.save(args.save); print("saved to", args.save)
        if args.gallery:
            try: n, m = w.export_gallery(args.gallery); print(f"gallery: {n} works, {m} songs -> {args.gallery}")
            except RuntimeError as ex: print(ex)
    else:
        run_gui(w, args.save, args.gallery)
