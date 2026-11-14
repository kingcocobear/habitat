# Habitat

A free, offline artificial-life world. Beings live in places, move around based on
their needs and personalities, learn skills, remember, and have children with
2 or 3 parents. No internet, no accounts, no money, and no paid AI required.

## What's here

| File | What it is |
|---|---|
| `habitat.py` | The main world: 11 places, beings with traits/skills/values/memories, a window to watch and inspect them |
| `poly_replication.py` | Standalone code for making a child from 2-3 parents |
| `companion_test.py` | Chat with a local language model (OLMo) through Ollama |
| `cosmos.py` | A procedurally generated universe: a seed number creates endless star systems. `habitat.py` sends bold beings out from the Wilds to explore it; it also runs on its own |
| `gallery.py` | Turns the beings' sketches, star charts and songs into one web page anyone can open (used by `habitat.py --gallery`) |
| `ternary.py` | Balanced ternary math: numbers written with three digits, minus, zero and plus, the way the Soviet Setun computer (1958) counted. `habitat.py` uses it for the beings' feelings about places; it also runs on its own |
| `test_ternary.py` | Checks for `ternary.py` and the feelings in `habitat.py`. Run `python test_ternary.py` |
| `pencil_lab.html` | The Pencil Lab: try the beings' pencil yourself (pressure, curve, grade, tilt, paper grain) and copy your settings into the habitat. Open it in any browser |
| `perception_test.py` | Habitat Perception Experiment 001: shows an AI the same place four ways (picture, picture made of 1s and 0s, text grid map, plain words) and scores which way it understands best, for how many tokens. Run `python perception_test.py --selftest`, then `--model YOUR_MODEL` |
| `gallery_example.html` | A finished example gallery from a 30,000-tick world. Open it in any browser, no Python needed. Press *listen* to hear the songs |
| `habitat_observe.html` | A separate browser experiment: do simple agents develop shared rhythm, "dialects," and groups? Open it in any browser |
| `README_IF_YOU_FIND_THIS.txt` | A plain-language note for anyone who finds this archive later |

## Run it

Needs Python 3. No installs for `habitat.py` (the window uses tkinter, which comes
with most Python installs; on Linux you may need `sudo apt install python3-tk`).

```bash
python habitat.py                              # open the window
python habitat.py --headless 20000 --seed 1    # no window, prints a summary
```

Click a being to see its traits, skills, values, parents, memories, tools and songs. The
**gallery** button writes `gallery.html` and opens it.

Make the gallery page from a headless run:

```bash
python habitat.py --headless 30000 --seed 1 --gallery gallery.html
```

Save and resume a world (it's plain JSON text, about 33 KB for 25 beings):

```bash
python habitat.py --save world.json                      # saves on close and every 2000 ticks
python habitat.py --load world.json --save world.json    # pick up where you left off
```

A resumed world continues exactly as if it had never stopped.

## How it works (short version)

- Each being re-decides where to go every 20-60 ticks, scoring each place by its
  needs (energy, loneliness) and personality. This is rule-based, so it's free.
- Children inherit blended traits, talent (half of a parent's skill), values
  (core values like safety never fade out), and tagged ancestral memories.
- Beings get bored, and bold, curious ones head for novel places. In the Wilds they can find
  things; in the Workshop they build tools that make hard work easier. Finders gain fame,
  and sociable beings are drawn to places where successful beings are.
- Everyone has a notebook and pencil. Beings gather materials (the Wilds, the Grove, the Shore), build
  pencils, notebooks and instruments in the Workshop, sketch beautiful places, and play and compose songs
  that others learn. The best sketches hang in the gallery.
- Bold, curious beings who have built something can launch from the Wilds into the generated universe in
  `cosmos.py`. They chart systems, bring back materials and discoveries, and some never return.
- The Archive holds notes beings leave and read, plus a legacy note for each death.
- `LLM_HOOK` in `habitat.py` is where a real language model could plug in later.

```bash
python cosmos.py                    # send explorers out and read what happened
python cosmos.py --system 3 -2 5    # describe one place in the universe
python cosmos.py --map 0            # ASCII star map
```

`habitat.py` imports `cosmos.py`, `gallery.py` and `ternary.py` when they sit in the same folder. Without them the habitat still runs, just with no expeditions, no gallery page and no feelings about places.

## Honest limits

The beings are simple programs. This is a toy world for studying how simple rules
produce group behavior, not a claim that anything here is conscious or alive.

## License

MIT. See `LICENSE`.


## Reactions and pilgrimages (added)
Beings now visit **The Gallery** (a place in the world) and react to each other's work by taste: they admire pieces,
get inspired to draw a reply, offer tips, and answer each other's songs with tunes of their own. Star charts mark real
coordinates of wonders; a curious being who studies a chart may set out to that wonder, follow the charted route, come
home, and draw what they saw, crediting the chart's artist. All of it appears in the gallery page (`--gallery FILE`).


## DNA scanner (added)
Explorers scan animals on life planets into a library, then borrow one trait (swift, tough, keen, strong, hardy) for a few
jumps when they need it. Each borrowed form costs supplies and adds strain; too much strain can hurt. In testing it gives
a small edge (about +2% survival, +14% haul), not a cheat code. Scanned creatures appear as field notes and sketches.

## Pixel people (added)
The window draws each being as a small pixel character (unique face, hair, skin; shirt shows the dominant trait). A button
switches back to dots.


## Guest minds (added)
Real AI minds can live in the habitat as guest beings, choosing where to go and saying one short sentence.
- Local model: `python habitat.py --ai olmo2:7b --ai-names Olmo` (needs Ollama running; never blocks the world if the model is slow).
- Any other program: `python habitat.py --serve 8765`, then see `guest_example.py` and the API at the top of `guests.py`.
Guests are told honestly that they are AI minds in a simulated world, can only choose a place and speak (160 characters,
rate-limited), cannot take over existing beings, are capped at 8, and the door listens on this computer only.

## Live viewer (added)
With `--serve 8765`, open http://127.0.0.1:8765/ in any browser to watch the habitat live with pixel people, click a being
to inspect it, and click a name in the chat to jump to them. Read only for viewers. It listens on this computer only.

Visitor (in the live viewer): walk with WASD or arrows (or tap the ground), Space to jump, Shift to roll, E to wave at a nearby being.
Waving is the only thing a human visitor can change in the world: it lifts that being's loneliness a little and becomes a memory.

Human visitors (live viewer): choose a name, hair style and colours; other humans and every AI guest can see you and your
chat line (100 characters, rate limited). Guests are told when a human visitor is in their place. Up to 20 visitors at once.
Nothing a visitor sends can do more than move, wave and speak. Before opening this to strangers, add moderation and an 18+ gate.

18+ gate (live viewer): before a person can appear, talk or wave, the page asks them to confirm they are 18 or older and that they
understand the beings are programs; the server refuses visits, speech and waves from anyone who has not confirmed. Chat blocks
links, emails and phone numbers, and an optional `blocked_words.txt` (one word per line) blocks more.
IMPORTANT: this is a self-declaration, not age verification, and the word filter is basic. Before inviting the public you need
real age assurance, real moderation (reporting, muting, logs, humans reviewing), and legal advice for where you operate.


## Ternary minds (added)
Beings now form feelings about places, and those feelings are counted in **balanced ternary**: each digit is `-` (minus one),
`0`, or `+` (plus one), the number system of the Soviet Setun computer. `ternary.py` does the arithmetic digit by digit.

- Each being keeps a small tally per place, six ternary digits long (for example `0000+-` is +2).
- Good moments add to it: a find in the Wilds (+3), a sketch that makes the gallery wall, playing for listeners, building
  something, meeting someone (+1 each).
- Bad moments subtract: a scare in the Wilds (-4), wearing yourself out (-2), being packed into a full place or being
  lonely and alone there (-1 each).
- The **sign** of the tally is the being's opinion: `+` likes the place, `0` no opinion, `-` would rather not. Only the sign
  counts when the being decides where to go, and it is a nudge (`FEEL_W` in `habitat.py`), not an order.
- Every five years of a being's life each feeling drifts one step back toward zero, so old joys and old scares wear off.

Click a being to see its feelings. They are saved with the world, and older save files still load. In testing over
8 worlds of 25,000 ticks, population, births, art and songs stayed in the same range as before; what changes is that
individual beings develop favourite places and places they steer clear of.

```bash
python ternary.py            # see balanced ternary in action
python ternary.py 42 -17     # write two numbers in ternary and add them
python test_ternary.py       # run the checks
```

This is ordinary software doing three-valued math on a normal computer. It is not a ternary chip and makes nothing faster.

## The pencil (added)
Every artist now draws with a real pencil model instead of plain lines. The same model runs in `pencil_lab.html`, where a human can feel it with a mouse, finger, stylus or drawing tablet.
- **Pressure** sets how wide and dark a stroke goes and how deep into the paper grain it reaches. A light touch only catches the tops of the grain, so it looks airy. A heavy press fills the grain in, so it goes smooth and dark.
- **Pressure curve** decides how pressure turns into graphite. **Grade** runs from 9H (light, crisp) to 9B (very dark). **Tilt** is the side of the lead. **Sharpness** wears down over a pencil's 25 sketches.
- Each being has its own pencil, picked from its name, and skilled artists vary their pressure more. The grade shows in each sketch's description.
- To hand everyone **your** pencil, open `pencil_lab.html` (or `/pencil` while `--serve` is running), tune it until it feels right, press **Copy settings for the habitat**, save the text as `pencil.json`, then run:
  `python habitat.py --headless 20000 --pencil pencil.json --gallery gallery.html`
  Every being then draws with your settings, each holding the pencil a little differently.
## Perception Experiment 001 (added)
What is the best way to show a habitat place to an AI guest? `perception_test.py` makes a small walled place (trees, a pond, food, other beings, and you) and shows it four ways:
- **picture**: a top-down image (needs a vision model such as `gemma3`, `llava` or `qwen2.5vl` in Ollama)
- **binary**: the same image, drawn entirely out of 1s and 0s
- **grid**: a text map, `#` for walls, `T` for trees, `~` for water, `F` for food, `@` for other beings and `A` for you
- **words**: a plain description, like guests get now

The AI answers the same 4-5 questions about each version: counting, what's nearest, which direction, which is farther, and whether there's a wall. It's scored on right answers, tokens used and seconds per answer.
```
python perception_test.py --selftest                      # checks the test itself, no model needed
python perception_test.py --save-scenes scenes/           # look at the scenes yourself
python perception_test.py --model gemma3:4b --scenes 10    # the real run
python perception_test.py --model qwen2.5:3b --text-only   # a model without vision: grid vs words
```
Every answer is saved to `perception_results.json`. Scenes come from seeds, so the same seeds give the same test every time, and two models can be compared fairly.

## Radios and hands-free calls (added)
**Radios in the world.** Beings can make a radio in the Workshop, and most explorers pack one before they leave. With a radio, a being sometimes calls a friend in another place to share its latest news, which helps with loneliness. Explorers call home when they find something. The farther they are from Home Haven, the more static eats their words (`f~un~ a p~rfectly r~und lake`), and past a certain distance only static gets through. Radio chatter is saved with the world.

**Hands-free calls.** A human in the live viewer (`--serve`) can pick any being and press 📻 **call** to ask it something.
- **AI guests** answer on a separate line, like a headset, so the call never pauses what they're doing in the world. They keep choosing places and acting while the answer comes back. The call goes into their memories.
- **Ordinary beings** answer from what they're doing and remember, if they have a radio. If they don't, the call says so.
- **Outside AI programs** pick up calls with `GET /calls?name=NAME` and answer with `POST /answer {"name", "call", "answer"}`, without stopping their `/act` loop.
- The same rules as chat apply: 18+ gate, no links or contact details, one call every few seconds, at most 3 calls waiting per guest, and a call drops after 2 minutes with no answer.
