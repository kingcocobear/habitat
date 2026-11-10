"""
Checks for ternary.py and the beings' ternary feelings in habitat.py.

    python test_ternary.py

Needs nothing but Python. Takes well under a minute.
"""
import json, os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ternary as T
import habitat as H

passed = 0

def ok(cond, what):
    global passed
    if not cond: raise SystemExit(f"FAILED: {what}")
    passed += 1
    print(f"  ok  {what}")

print("ternary.py")
ok(T.self_test() > 40000, "ternary arithmetic, logic and tally self-test")

print("habitat.py feelings")
ok(H.TERNARY is T, "habitat found ternary.py")

w = H.World(seed=5)
a = w.agents[0]
ok(a.feelings == {} and w.opinion(a, "The Shore") == 0, "a new being has no opinions")

w.feel(a, "The Shore", 1, 3)
ok(a.feelings["The Shore"] == "0000+0" and w.opinion(a, "The Shore") == 1, "good times make a liking (+3 is 0000+0)")
w.feel(a, "The Wilds", -1, 4)
ok(a.feelings["The Wilds"] == "0000--" and w.opinion(a, "The Wilds") == -1, "a scare makes a dislike (-4 is 0000--)")
w.feel(a, "Nowhere", 1)
ok("Nowhere" not in a.feelings, "feelings about places that do not exist are ignored")

occ = {p: [] for p in H.PLACES}
for x in w.agents: occ[x.place].append(x)
def score_with(pn, text):
    saved = dict(a.feelings)
    a.feelings = {pn: text} if text else {}
    v = w.score(a, pn, H.PLACES[pn], occ)
    a.feelings = saved
    return v
base, liked, disliked = score_with("The Shore", None), score_with("The Shore", "00000+"), score_with("The Shore", "00000-")
ok(abs(liked - base - H.FEEL_W) < 1e-9 and abs(base - disliked - H.FEEL_W) < 1e-9,
   "a liking pulls a being toward a place and a dislike pushes it away, by FEEL_W")
ok(abs(score_with("The Shore", "++++++") - liked) < 1e-9, "only the sign counts: a huge liking pulls no harder than a small one")

w.fade(a)
ok(a.feelings == {"The Shore": "0000+-", "The Wilds": "0000-0"}, "fading moves every feeling one step toward 0")
for _ in range(5): w.fade(a)
ok(a.feelings == {}, "feelings fade away completely and are then forgotten")

text = w.feelings_text(a)
w.feel(a, "The Grove", 1)
ok(text == "none yet" and w.feelings_text(a) == "The Grove 00000+ likes", "the inspector line reads cleanly")

print("habitat.py long run")
w = H.World(seed=11)
for _ in range(9000): w.tick()
felt = [x for x in w.agents if x.feelings]
signs = {w.opinion(x, p) for x in felt for p in x.feelings}
ok(len(felt) >= 5 and signs == {1, -1}, "after 90 years beings hold both likings and dislikes")
ok(all(len(v) == 6 and set(v) <= set("+0-") and p in H.PLACES for x in felt for p, v in x.feelings.items()),
   "every stored feeling is a 6-trit tally about a real place")

d = tempfile.mkdtemp()
path = os.path.join(d, "world.json")
w.save(path)
for _ in range(4000): w.tick()
straight = json.dumps(w.to_dict(), sort_keys=True)
w2 = H.World.load(path)
for _ in range(4000): w2.tick()
ok(straight == json.dumps(w2.to_dict(), sort_keys=True), "a saved and resumed world continues exactly the same")

old = json.load(open(path))
for x in old["agents"]: x.pop("feelings")
old["agents"][0]["feelings"] = {"Nowhere": "+++", "The Wilds": "2x", "The Shore": "", "The Grove": 5, "The Stage": "000+0-"}
json.dump(old, open(path, "w"))
w3 = H.World.load(path)
ok(w3.agents[0].feelings == {"The Stage": "000+0-"} and all(x.feelings == {} for x in w3.agents[1:]),
   "older saves without feelings load, and damaged feelings are dropped")
for _ in range(1000): w3.tick()
ok(len(w3.agents) > 0, "a world loaded from an older save keeps running")

saved_T, H.TERNARY = H.TERNARY, None
w4 = H.World(seed=3)
for _ in range(3000): w4.tick()
ok(all(x.feelings == {} for x in w4.agents) and len(w4.agents) > 0, "without ternary.py the habitat still runs, just with no feelings")
H.TERNARY = saved_T

os.remove(path); os.rmdir(d)
print(f"\nall {passed} checks passed")
