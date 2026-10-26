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

`habitat.py` imports `cosmos.py` and `gallery.py` when they sit in the same folder. Without them the habitat still runs, just with no expeditions and no gallery page.

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
