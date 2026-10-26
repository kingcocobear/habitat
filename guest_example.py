"""
A tiny example of an outside program (or AI) joining the habitat as a guest. Standard library only.

1. In one terminal:   python habitat.py --serve 8765
2. In another:        python guest_example.py Pip

Replace choose() with a call to any model or program you like. It gets plain text describing the scene and answers
with a place and one short sentence. That is all a guest can do, by design.
"""
import json, random, sys, time, urllib.request

BASE = "http://127.0.0.1:8765"; NAME = sys.argv[1] if len(sys.argv) > 1 else "Pip"

def call(path, data=None):
    req = urllib.request.Request(BASE + path, json.dumps(data).encode() if data is not None else None)
    with urllib.request.urlopen(req, timeout=10) as r: return json.load(r)

def choose(obs):
    """Your mind goes here. obs['scene'] is the situation in words; obs['places'] lists where you can go."""
    place = random.choice(obs["places"])
    return place, f"I think I'll visit {place}."

print(call("/join", {"name": NAME}))
while True:
    obs = call(f"/observe?name={NAME}")
    place, say = choose(obs)
    call("/act", {"name": NAME, "go": place, "say": say})
    print(NAME, "->", place)
    time.sleep(5)
