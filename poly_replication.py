"""
Poly replication: make a child from 2-3 parents. No dependencies.
Blends traits, skills, values, and memories, with small random mutation.
"""
import random, json

TRAITS = ["curiosity", "sociability", "caution", "energy", "creativity"]
CORE_VALUES = {"safety"}      # always passed down if any parent has it
_counter = 0

def clamp(x): return max(0.0, min(1.0, x))

def dirichlet(n):
    g = [random.gammavariate(1, 1) for _ in range(n)]
    return [x / sum(g) for x in g]

def make_child(parents, mutation_rate=0.12, mutation_size=0.06):
    global _counter; _counter += 1
    w = dirichlet(len(parents))            # random shares that sum to 1
    child = {"id": f"child_{_counter}", "parents": [p["id"] for p in parents],
             "weights": [round(x, 2) for x in w],
             "traits": {}, "skills": {}, "memories": [], "values": {}}

    # 1. traits: weighted blend + occasional mutation
    for t in TRAITS:
        v = sum(wi * p["traits"].get(t, 0.5) for wi, p in zip(w, parents))
        if random.random() < mutation_rate: v += random.gauss(0, mutation_size)
        child["traits"][t] = round(clamp(v), 3)

    # 2. skills: blend, boosted toward the best parent so rare skills survive
    #    (halved: a child inherits talent, not finished expertise)
    for k in {k for p in parents for k in p.get("skills", {})}:
        blend = sum(wi * p.get("skills", {}).get(k, 0) for wi, p in zip(w, parents))
        best = max(p.get("skills", {}).get(k, 0) for p in parents)
        prof = 0.4 * blend + 0.6 * best
        if random.random() < min(0.95, prof + 0.3):
            if random.random() < mutation_rate: prof += random.gauss(0, mutation_size)
            child["skills"][k] = round(clamp(prof) * 0.5, 3)

    # 3. values: blend; core values never dilute away
    for k in {k for p in parents for k in p.get("values", {})}:
        v = sum(wi * p.get("values", {}).get(k, 0) for wi, p in zip(w, parents))
        if k in CORE_VALUES and v > 0: v = max(v, 0.3)
        if v > 0.12:
            if random.random() < mutation_rate: v += random.gauss(0, mutation_size)
            child["values"][k] = round(clamp(v), 3)

    # 4. memories: inherited as ancestral knowledge, tagged with the source
    for wi, p in zip(w, parents):
        mems = p.get("memories", [])
        if mems:
            for m in random.sample(mems, min(max(1, round(wi * 4)), len(mems))):
                child["memories"].append(m if m.startswith("[from") else f"[from {p['id']}] {m}")
    child["memories"] = list(dict.fromkeys(child["memories"]))[:8]
    if child["memories"] and random.random() < mutation_rate:
        i = random.randrange(len(child["memories"]))
        child["memories"][i] = child["memories"][i].replace(" (mutated)", "") + " (mutated)"
    return child

if __name__ == "__main__":
    A = {"id": "A", "traits": dict(curiosity=.9, sociability=.2, caution=.5, energy=.7, creativity=.4),
         "skills": {"physics": .85, "coding": .7}, "values": {"truth-seeking": .95, "safety": .4},
         "memories": ["Studied gravitational anomalies"]}
    B = {"id": "B", "traits": dict(curiosity=.3, sociability=.8, caution=.6, energy=.5, creativity=.9),
         "skills": {"storytelling": .85}, "values": {"connection": .9},
         "memories": ["Grew up in a large community"]}
    C = {"id": "C", "traits": dict(curiosity=.6, sociability=.5, caution=.2, energy=.9, creativity=.6),
         "skills": {"engineering": .88, "physics": .55}, "values": {"progress": .95},
         "memories": ["Survived risky experiments"]}
    print(json.dumps(make_child([A, B, C]), indent=2))
