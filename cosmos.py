"""
COSMOS - a procedurally generated universe for the habitat's explorers.
Free, offline, no dependencies. Nothing is stored: a seed number plus
coordinates creates every star system on demand, so the same seed always
gives the same universe, and it is effectively endless.

  python cosmos.py                         # send 6 explorers out, print the story
  python cosmos.py --seed 7 --explorers 10 --steps 120
  python cosmos.py --system 3 -2 5         # describe the system at x=3 y=-2 z=5
  python cosmos.py --map 0                 # ASCII map of the slice z=0
"""
import hashlib, math, random, argparse

TRAITS = ["curiosity", "sociability", "caution", "energy", "creativity"]
HOME = (0, 0, 0)
DENSITY = 0.30          # chance a cell holds a star system
MAX_JUMP = 4.0          # longest single jump (cells)

# name, weight, luminosity, fuel from scooping, hazard damage when scooping
STARS = [("red dwarf", .40, .3, 6, 0), ("orange dwarf", .18, .6, 10, 0),
         ("yellow dwarf", .20, 1.0, 12, 0), ("white star", .08, 2.5, 14, 3),
         ("red giant", .06, 4.0, 10, 8), ("blue giant", .04, 12.0, 10, 12),
         ("neutron star", .04, .1, 0, 22)]

# type: (base hazard, resource profile)
PTYPES = {
    "lava":      (.80, dict(metals=.8, crystal=.5)),
    "desert":    (.30, dict(metals=.5, crystal=.4)),
    "ocean":     (.15, dict(water=.9, organics=.5)),
    "jungle":    (.30, dict(organics=.9, water=.5)),
    "ice":       (.35, dict(water=.8, crystal=.4)),
    "barren":    (.25, dict(metals=.7, crystal=.3)),
    "rocky":     (.15, dict(metals=.6, water=.4, organics=.2)),
    "gas giant": (.60, dict(fuel_gas=.9)),
}
RARE = ["ancient ruins", "crystal caves", "a singing canyon", "floating islands",
        "a glowing sea", "a buried machine", "giant bones", "a perfectly round lake"]
LIFE_WORLDS = {"ocean": .55, "jungle": .65, "rocky": .25, "ice": .08}

def rng_for(seed, *key):
    h = hashlib.blake2b(repr((seed,) + key).encode(), digest_size=8).digest()
    return random.Random(int.from_bytes(h, "big"))

def make_name(r):
    on, v = "bdgklmnprstvz", "aeiou"
    n = "".join(r.choice(on) + r.choice(v) for _ in range(r.choice([2, 2, 3])))
    return (n + r.choice(["", "", "n", "x", "r", "s"])).capitalize()

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]

class Cosmos:
    def __init__(s, seed=1):
        s.seed, s._cache = seed, {}

    def system(s, x, y, z):
        key = (x, y, z)
        if key not in s._cache: s._cache[key] = s._make(x, y, z)
        return s._cache[key]

    def _make(s, x, y, z):
        r = rng_for(s.seed, "sys", x, y, z)
        home = (x, y, z) == HOME
        if not home and r.random() > DENSITY: return None
        name = "Home Haven" if home else make_name(r)
        star = (STARS[2] if home else
                r.choices(STARS, [t[1] for t in STARS])[0])
        lum = star[2]
        planets = []
        for i in range(r.randint(2, 4) if home else r.choice([0, 1, 2, 2, 3, 3, 4, 5, 6])):
            planets.append(s._planet(r, name, i, lum))
        return dict(name=name, coords=(x, y, z), star=star[0], fuel=star[3],
                    star_hazard=star[4], planets=planets)

    def _planet(s, r, sysname, i, lum):
        au = 0.3 * 1.8 ** i * (0.7 + 0.6 * r.random()) * lum ** 0.25
        temp = 278 * lum ** 0.25 / math.sqrt(au)
        if temp > 700:   opts = [("lava", 60), ("barren", 25), ("gas giant", 15)]
        elif temp > 400: opts = [("desert", 50), ("barren", 30), ("lava", 10), ("gas giant", 10)]
        elif temp > 250: opts = [("rocky", 30), ("ocean", 25), ("jungle", 20), ("desert", 15), ("barren", 10)]
        elif temp > 150: opts = [("ice", 40), ("rocky", 25), ("barren", 15), ("ocean", 10), ("gas giant", 10)]
        else:            opts = [("ice", 40), ("gas giant", 35), ("barren", 25)]
        ptype = r.choices([o[0] for o in opts], [o[1] for o in opts])[0]
        gravity = round(r.uniform(2.0, 4.0) if ptype == "gas giant" else r.uniform(.3, 2.0), 2)
        atm = {"lava": ["toxic", "crushing"], "gas giant": ["crushing"], "barren": ["none", "none", "thin"],
               "ice": ["thin", "none"], "desert": ["thin", "toxic", "breathable"],
               "ocean": ["breathable", "breathable", "thin"], "jungle": ["breathable", "toxic"],
               "rocky": ["thin", "breathable", "toxic"]}[ptype]
        atmosphere = r.choice(atm)
        base, prof = PTYPES[ptype]
        hazard = base + {"toxic": .2, "crushing": .3}.get(atmosphere, 0) + (.15 if gravity > 1.5 else 0) + r.random() * .2
        life = "none"
        if ptype in LIFE_WORLDS and r.random() < LIFE_WORLDS[ptype] and atmosphere != "crushing":
            life = r.choices(["microbial", "plants", "animals", "signs of intelligence"], [50, 30, 18, 2])[0]
        return dict(name=f"{sysname} {ROMAN[i]}", type=ptype, temp=int(temp), gravity=gravity,
                    atmosphere=atmosphere, hazard=round(min(1, hazard), 2),
                    resources={k: round(min(1, v * r.uniform(.4, 1.2)), 2) for k, v in prof.items()},
                    life=life, rare=r.choice(RARE) if r.random() < .025 else None)

    def nearby(s, pos, radius):
        px, py, pz = pos; out = []
        R = int(math.ceil(radius))
        for x in range(px - R, px + R + 1):
            for y in range(py - R, py + R + 1):
                for z in range(pz - R, pz + R + 1):
                    if (x, y, z) != pos and math.dist((x, y, z), pos) <= radius:
                        sy = s.system(x, y, z)
                        if sy: out.append(sy)
        return out

    def describe(s, x, y, z):
        sy = s.system(x, y, z)
        if not sy: return f"({x},{y},{z}): empty space."
        lines = [f"{sy['name']} at ({x},{y},{z}) - {sy['star']}, {len(sy['planets'])} planet(s)"]
        for p in sy["planets"]:
            extra = (f", life: {p['life']}" if p["life"] != "none" else "") + (f", RARE: {p['rare']}" if p["rare"] else "")
            lines.append(f"  {p['name']}: {p['type']}, {p['temp']}K, {p['atmosphere']} air, "
                         f"hazard {p['hazard']}{extra}")
        return "\n".join(lines)

    def ascii_map(s, z, R=14):
        rows = []
        for y in range(-R, R + 1):
            rows.append("".join("@" if (x, y, z) == HOME else ("*" if s.system(x, y, z) else ".")
                                for x in range(-R, R + 1)))
        return "\n".join(rows)

# ---- DNA scanner: scan animals on life planets, borrow one trait for a few jumps, pay a strain price ----
FORMS = {   # trait: what it does while borrowed
    "swift": "jumps cost 25% less fuel", "tough": "landings hurt 40% less", "keen": "spots dangers (landings hurt 25% less) and gathers 30% more",
    "strong": "carries 60% more cargo", "hardy": "supplies last twice as long",
}
FORM_JUMPS, FORM_COST = 6, 2.0
_SYL = ["ka", "lo", "mi", "ru", "ze", "ta", "vo", "ni", "shu", "bre", "thal", "pi", "gor", "yu", "sen", "wo"]
_KIND = ["glider", "stalker", "grazer", "burrower", "darter", "wader", "climber", "drifter", "hopper", "lurker"]

def species_of(p):
    """The animal living on a planet is always the same one, drawn from the planet's name."""
    r = rng_for(0, "species", p["name"])
    name = "".join(r.choice(_SYL) for _ in range(2)).capitalize() + " " + r.choice(_KIND)
    return name, r.choice(list(FORMS))

class Explorer:
    def __init__(s, name, traits, rng):
        s.name, s.t, s.r = name, traits, rng
        s.skill = round(rng.uniform(.1, .4), 2)       # exploration skill, grows with experience
        s.pos, s.fuel, s.supplies, s.health = HOME, 40.0, 60.0, 100.0
        s.cargo = {}; s.store = {}
        s.visited, s.log, s.discoveries = set(), [], []
        s.alive, s.cause, s.jumps, s.landings, s.trips, s.far = True, "", 0, 0, 0, 0.0
        s.wonders = []                 # [[x, y, z], "a singing canyon on Bopo I"] for everything rare or alive they found
        s.goal, s.route = None, set()  # a pilgrim heads for one charted wonder, preferring systems on the chart
        s.reached, s.homebound, s.meta = False, False, {}
        s.dna = {}                     # species name -> {"trait": ..., "planet": ...}, the scanner library
        s.form, s.form_left, s.strain = None, 0, 0
        s.scans, s.morphs, s.backlashes = 0, 0, 0

    def note(s, text): s.log.append(text)

    def dock(s):
        for k, v in s.cargo.items(): s.store[k] = round(s.store.get(k, 0) + v, 2)
        s.cargo = {}; s.fuel, s.supplies, s.health = 40.0, 60.0, 100.0; s.trips += 1
        s.form, s.form_left, s.strain = None, 0, max(0, s.strain - 3)     # a rest at home settles the body
        s.note(f"{s.name} returned to Home Haven (trip {s.trips}).")

    def go(s, W, target):
        d = math.dist(s.pos, target)
        cost = d * (.75 if s.form == "swift" else 1.0)
        if cost > s.fuel:
            s.alive, s.cause = False, "adrift, out of fuel"; s.note(f"{s.name} ran out of fuel and drifted away."); return
        s.fuel -= cost; s.supplies -= .5 if s.form == "hardy" else 1; s.pos = target; s.jumps += 1
        s.tick_form()
        s.far = max(s.far, math.dist(target, HOME))
        if s.supplies > 20: s.health = min(100, s.health + 5)
        if s.supplies <= 0: s.alive, s.cause = False, "ran out of supplies"; s.note(f"{s.name} ran out of supplies."); return
        if target == HOME: s.dock(); return
        sy = W.system(*target)
        if sy and target not in s.visited: s.arrive(sy)

    def tick_form(s):
        if not s.form: return
        s.form_left -= 1
        if s.form_left <= 0:
            s.note(f"{s.name} let the {s.form} form fade.")
            if s.strain >= 3 and s.r.random() < .5:                    # too many borrowed forms in a row
                s.backlashes += 1; s.note(f"{s.name} felt the strain of borrowed forms.")
                s.form = None; s.hurt(8 * (1 - .5 * s.skill), "strain from borrowed forms"); return
            s.form = None

    def need_form(s):
        """Pick a form from the library only when it would really help right now."""
        if s.form or not s.dna or not s.alive or s.supplies < FORM_COST + 8: return
        dh = math.dist(s.pos, HOME)
        have = {v["trait"] for v in s.dna.values()}
        want = None
        if s.health < 55 and "tough" in have: want = "tough"
        elif dh > 6 and s.fuel < dh * 1.3 + 6 and "swift" in have: want = "swift"
        elif dh > 6 and s.supplies < 28 and "hardy" in have: want = "hardy"
        elif s.cargo and sum(s.cargo.values()) < 6 and s.fuel > 25 and "strong" in have and s.r.random() < .05: want = "strong"
        if want and s.strain < 5 and s.r.random() < .5 + .4 * (1 - s.t["caution"]):
            s.form, s.form_left = want, FORM_JUMPS; s.supplies -= FORM_COST; s.strain += 1; s.morphs += 1
            s.note(f"{s.name} took the {want} form ({FORMS[want]}).")

    def scan(s, p):
        sp, trait = species_of(p)
        if sp in s.dna or p["life"] != "animals": return
        if s.r.random() < (.3 + .5 * s.t["curiosity"]) * (.6 + .4 * s.skill) and s.supplies > 8:
            s.supplies -= 1; s.dna[sp] = {"trait": trait, "planet": p["name"]}; s.scans += 1
            s.note(f"{s.name} scanned a {sp} on {p['name']} ({trait}).")

    def hurt(s, amount, why):
        s.health -= amount
        if s.health <= 0 and s.alive:
            s.alive, s.cause = False, why; s.note(f"{s.name} was lost: {why}.")

    def arrive(s, sy):
        s.visited.add(sy["coords"])
        s.note(f"{s.name} charted {sy['name']} ({sy['star']}, {len(sy['planets'])} planets) at {sy['coords']}.")
        if sy["fuel"] and (sy["star_hazard"] == 0 or s.fuel < 20):     # only scoop dangerous stars when desperate
            s.fuel = min(40.0, s.fuel + sy["fuel"])
            if sy["star_hazard"]: s.hurt(sy["star_hazard"] * (1 - .5 * s.skill) * s.r.uniform(.5, 1.3), f"burned scooping {sy['star']}")
        if s.goal is not None and not s.reached:        # a pilgrim travels light: no landings until the goal
            if tuple(sy["coords"]) != tuple(s.goal): return
            for p in sy["planets"]:
                if not s.alive: return
                if p["rare"] or p["life"] in ("animals", "signs of intelligence"): s.land(p)
            return
        for p in sy["planets"]:
            if not s.alive: return
            if p["rare"]: s.found(p, f"{p['rare']} on {p['name']}")
            if p["life"] in ("animals", "signs of intelligence"): s.found(p, f"{p['life']} on {p['name']}")
            want = ((.3 + .6 * s.t["curiosity"]) * (1 - p["hazard"] * (.5 + s.t["caution"]))
                    * min(1, s.health / 60))      # hurt explorers play it safe
            if s.r.random() < want * (.5 if p["type"] == "gas giant" else 1):
                s.land(p)

    def found(s, p, text):
        entry = f"{text} at {p['name'].rsplit(' ', 1)[0]}"
        if entry not in s.discoveries:
            s.discoveries.append(entry); s.wonders.append([list(s.pos), text]); s.note(f"{s.name} discovered {text}!")

    def land(s, p):
        s.landings += 1; s.supplies -= 1.5
        guard = {"tough": .6, "keen": .75}.get(s.form, 1.0)
        s.hurt(p["hazard"] * 22 * guard * (1 - .5 * s.skill) * s.r.uniform(.5, 1.3), f"killed on {p['name']} ({p['type']}, hazard {p['hazard']})")
        if not s.alive: return
        s.skill = min(1.0, round(s.skill + .01, 3))
        s.scan(p)
        haul = {"strong": 1.6, "keen": 1.3}.get(s.form, 1.0)
        for k, v in p["resources"].items():
            if v > .4: s.cargo[k] = round(s.cargo.get(k, 0) + v * (.5 + s.t["energy"]) * haul, 2)
        if p["resources"].get("water", 0) > .6 or p["resources"].get("organics", 0) > .6:
            s.supplies = min(60.0, s.supplies + 8)
        if p["resources"].get("fuel_gas", 0) > .6: s.fuel = min(40.0, s.fuel + 10)

    def seek(s, W, margin):
        """One jump toward the goal, always closer than before, preferring systems that are on the chart."""
        dg, best = math.dist(s.pos, s.goal), None
        for sy in W.nearby(s.pos, min(MAX_JUMP, s.fuel)):
            c = sy["coords"]; d = math.dist(s.pos, c)
            if s.fuel - d < math.dist(c, HOME) * margin + 2: continue
            gap = math.dist(c, s.goal)
            if gap >= dg - .2: continue
            score = -gap + (1.0 if c in s.route else 0.0) + s.r.random() * .3
            if best is None or score > best[0]: best = (score, c)
        if best is None:
            s.homebound = True; s.note(f"{s.name} could not find a safe way on and turned back."); return
        s.go(W, best[1])
        if s.alive and s.pos == tuple(s.goal):
            s.reached, s.homebound = True, True; s.note(f"{s.name} arrived at the place on the chart.")

    def step(s, W):
        if not s.alive: return
        dh = math.dist(s.pos, HOME)
        s.need_form()
        margin = 1.15 + .6 * s.t["caution"]
        if s.fuel <= dh * margin + 2 or s.supplies <= math.ceil(dh / MAX_JUMP) * 1.2 + 8:
            s.go(W, s.toward_home()); return
        if s.homebound: s.go(W, s.toward_home()); return
        if s.goal is not None and not s.reached: s.seek(W, margin); return
        cands = []
        for sy in W.nearby(s.pos, min(MAX_JUMP, s.fuel)):
            c = sy["coords"]; d = math.dist(s.pos, c)
            if s.fuel - d < math.dist(c, HOME) * margin + 2: continue
            score = (s.t["curiosity"] * (1.0 if c not in s.visited else -.8) + .08 * len(sy["planets"])
                     + (.3 if sy["fuel"] and s.fuel < 20 else 0) - .05 * d * s.t["caution"] + s.r.random() * .4)
            if c == HOME: score -= 5
            cands.append((score, c))
        if not cands:
            s.go(W, s.toward_home() if s.r.random() < .5 else s.outward()); return
        best = max(cands)[1]
        s.go(W, best)

    def toward_home(s):
        d = math.dist(s.pos, HOME)
        if d <= MAX_JUMP: return HOME
        f = MAX_JUMP / d
        return tuple(int(round(c * (1 - f))) for c in s.pos)

    def outward(s):
        ang = s.r.uniform(0, 2 * math.pi); el = s.r.uniform(-.5, .5)
        return (s.pos[0] + int(round(3 * math.cos(ang))), s.pos[1] + int(round(3 * math.sin(ang))),
                s.pos[2] + int(round(3 * el)))

def run(seed, n, steps, verbose=True):
    W = Cosmos(seed); r = random.Random(seed + 1000)
    crew = [Explorer(make_name(r), {t: round(r.random(), 2) for t in TRAITS}, random.Random(r.random()))
            for _ in range(n)]
    for e in crew:
        for _ in range(steps): e.step(W)
    return W, crew

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--explorers", type=int, default=6)
    ap.add_argument("--steps", type=int, default=80)
    ap.add_argument("--system", type=int, nargs=3, metavar=("X", "Y", "Z"))
    ap.add_argument("--map", type=int, metavar="Z")
    a = ap.parse_args()
    if a.system: print(Cosmos(a.seed).describe(*a.system))
    elif a.map is not None: print(Cosmos(a.seed).ascii_map(a.map))
    else:
        W, crew = run(a.seed, a.explorers, a.steps)
        for e in crew:
            fate = "alive" if e.alive else f"LOST ({e.cause})"
            print(f"{e.name:10s} cur={e.t['curiosity']:.2f} cau={e.t['caution']:.2f} | {fate} | "
                  f"charted {len(e.visited)}, landings {e.landings}, trips {e.trips}, furthest {e.far:.1f}")
            for d in e.discoveries: print("     found", d)
