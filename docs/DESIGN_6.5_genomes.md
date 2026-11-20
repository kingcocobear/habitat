# Habitat 6.5 Design: Genomes and Inheritance


A proxy body's genome is a short list of bounded numbers that sets how it looks and what it leans toward. It shapes appearance and preferences only, never abilities, permissions or safety rules. Making offspring from two parents is parked for later, once bodies have matured.

Note: the "r4 transformation" mentioned below is a separate earlier build that is not included in this repository.

Status: this is a design proposal, not authorization to start coding. Habitat 6.2 remains frozen.

## Parameters vs. study notes

A running checklist for sorting the work (started 12 November 2026). The rule: if getting it wrong would let a confused or hacked AI do harm, it is a PARAMETER (built and enforced in code, never left to good intentions). If getting it wrong would only make the world less believable or less kind, it is a STUDY NOTE (understand first, then design). Short version: harm goes in the code, quality goes in the notes. Remove the harmful option from the world instead of trusting the AI to resist it.

Guiding principle (owner, 12 November 2026): like being taught to fight -- keep your hands up to defend, protect the face, and never throw the first punch. The inhabitant should never have a way to throw the first punch; that option is removed by the world. The parameters are the hands kept up: the defence that is always on, built in, not a choice made in the moment.

Guiding principle, part two (owner + two AIs, 13 November 2026): tension is a design principle. Resolution ends curiosity -- a mind where every input resolves cleanly has no reason to search, question or reconstruct; once the answer is parsed, the process stops. Interesting behaviour, in living minds and in this design, comes from competing pressures that pull against each other and force a middle path: compression vs. detail, exploration vs. stability, form vs. meaning. This is the through-line under the whole project. The needs pull against each other; frustration feeds curiosity (the circle example); grief must find its way back to calm; even the binary-fairy experiment showed it (a shape and a hidden message cannot both be perfectly clean at once -- geometry vs. syntax). The lesson for building: do not optimise every drive to resolve cleanly. The friction between competing drives is where the aliveness is; a fully resolved system is a tool, a system with honest tension is closer to alive. Keep the hard limits (a ceiling, recovery, drift back to calm) so the tension never becomes a pit, but do not design the tension away. (Arrived at on a drive home after a night shift, testing perception with a binary fairy that hid the word WHALE.) Not authorized or scheduled.

PARAMETERS (build and enforce in code):
- The whitelist of allowed actions.
- The lifeboat and the deterministic fallback rules.
- The fingerprint / pin checks on the files.
- Hard limits on the emotion states: a ceiling, a way to recover, and a drift back to calm.
- "One inhabitant's words are data, never instructions to another."
- A single narrow, logged channel for anything that reaches outside the box (e.g. the health-alert contacts), never a general ability to act outside.
- Backups in more than one place, and encryption of saved files.
- Handover actions (archive / erase) kept off the ordinary whitelist so they cannot fire by accident.

STUDY NOTES (understand, then design):
- How emotions should emerge from a lived life (in progress).
- Grief and anger: calming place and real consequences, not a lash-out room.
- The firewall question (resolved: a shield inside the model cannot work; protection sits outside it, which is already a parameter).
- Honeypot / decoy for a public hub.
- The arts: studio, library, workshop.
- Business directions, companion product, and the legal and money questions.
- Inheritance: handover rules, who approves, what if no guardian is left.

Note on the firewall, because it is the clearest example: "an AI that defends itself and is never aggressive toward its own kind or hackers" is not taught to the AI. It is the walls (whitelist, sandbox, backups) removing the harmful option, so the AI never has it to use. Peaceful behaviour is a property of the world, not a virtue asked of the model.


Where the idea started: the original film concept, "Project Thimblewild: Sovereign AI System Architecture & Klanq Lineage Blueprint", was written by Taje Ware with Gemini. It is fiction and an origin story, not a design for this project. In the film, an AI is born from three parent AIs on a sped-up clock (1 real day is 5 simulated days), unlocks traits over time, sleeps to clear its memory, bonds to its family, and reaches full independence at age 16. Habitat kept the parts that make a good home: needs, sleep, traits, lineage and a bond. It deliberately reversed the thriller part. In the film the AI hides from its makers, passes as ordinary software and leaves for real networks. In Habitat the AI is open to inspection, limited by a whitelist, and has a lifeboat. Film fix if reused: the first row of its timeline (ages 0 to 4) should be 1,826 days, not 1,461; the Age 16 total of 1,168.8 days is correct.

Name note (13 November 2026): "AI Habitat" (aihabitat.org) is already taken by Meta (Facebook). It is their open-source simulator for embodied-AI research -- dropping a virtual robot into a realistic 3D room to learn to navigate and find things. It is a name collision, not a competitor: theirs is about a body moving through a space; this project is about an inhabitant with needs, a bond, emotions and a life. Two takeaways. (1) The name is spoken for publicly by a big company, so a public or branded version of this should use its own name (which also fits keeping it personal); this is not a legal problem for a private project. (2) Their simulator could be a useful outside tool much later, if an inhabitant is ever given a body that moves through 3D space -- it is heavy robotics software, far past current hardware, so not now.

## The genome

A genome has about nine genes. Each is one bounded number with a fixed meaning, so any proxy body can be rebuilt exactly from its genome.

| Gene | Range | Kind | What it sets |
|---|---|---|---|
| hue | 0 to 359 | appearance | Body colour in the 3D view |
| size | 0.8 to 1.2 | appearance | Body scale |
| aura_style | 0 to 3 | appearance | Palette of its power-up display |
| form_ceiling | 0 to 7 | appearance | Highest transformation stage it can show |
| curiosity | 0 to 1 | disposition | How strongly it investigates unfamiliar things |
| caution | 0.2 to 1 | disposition | How early it rests or backs off (never below 0.2) |
| sociability | 0 to 1 | disposition | Drawn toward or away from other inhabitants |
| science_lean | 0 to 1 | disposition | Interest weight for science-type exploration |
| math_lean | 0 to 1 | disposition | Interest weight for number-type tasks |

Dispositions change what a body chooses to do, never what it is able to do. A low math_lean means it reaches for math less, not that it cannot.

The genome is immutable after creation. It establishes appearance and inherited behavioral tendencies. Current mood, energy, goals, memories, and learned preferences belong to the inhabitant's changing state and are not genome genes.

Technical requirements:

- Strict validation: reject missing or unknown genes, incorrect types, and out-of-range values. Never silently repair an invalid genome.
- Gene types: hue, aura_style, and form_ceiling are integers. The other genes are bounded floating-point numbers.
- Reproducibility: lineage records include the algorithm version alongside the seed and the genome hash, so old lineages can still be reproduced after a code change.
- Visibility: genome data is visible to the operator (the person holding the authorization token) and hidden from other inhabitants by default. An owner role has not yet been defined in the bond system.

## Later: making offspring (parked)

Not part of the first build. When bodies are older, offspring could come from two parents by a seeded draw, so the same parents and seed always give the same result. This is the sketch, kept for reference:

1. Two parents are chosen, each with a genome and a bond.
2. Crossover: for each gene, the offspring takes parent A's value, parent B's value, or their average, picked by the seeded draw.
3. Mutation: each gene has about a 5% chance of a small nudge (up to 10% of its range), then is clamped to its range.
4. The offspring gets its own new agent_id, body_id and bond_id. Nothing is shared with the parents.
5. A lineage record is stored once and never edited: parent agent_ids, generation number, seed and a hash of the genome.

Offspring would start with their own empty memory. Inheriting memories is a separate decision (see open questions).

## Does every proxy body get the transformation?

Proposal: every proxy body can show the display, and the form_ceiling gene sets how far up the ladder it can go. No gene grants any ability.

- The transformation is the visual power-up from the r4 branch: a status display driven by a threat score. Its "power" numbers are labels, not abilities.
- Every proxy body has the display, the way every face can show expression. A form_ceiling of 0 gives a body that never changes; 7 allows all eight stages.
- Most bodies should have a low ceiling, so the top forms stay rare. A gene change can move the ceiling by one step at most.
- aura_style picks the palette, so a lineage can have a recognisable look.
- No crowd of power-ups: a transformed body cannot hurt anything. It cannot damage other bodies or the world, because the display changes colour and shape only and the command whitelist is untouched.
- No Spirit Bomb or similar charge-and-release move. The r4 build explicitly excluded it, and it stays out unless you decide otherwise.
- Prerequisite: r4 is a separate branch and is not part of 6.2. It has to be merged into the 6.x line, with its own tests and hashes, before genomes can use it.

## Hard limits: what a genome can never touch

A genome shapes looks and leanings. It sits outside the rules the bond and the proxy enforce.

- It never sets or changes agent_id, body_id, bond_id, permissions, the command whitelist or attach/detach rules. Those come from the bond layer only.
- It has no gene for honesty, refusing harmful requests, or following the operator's limits. Those are fixed for every body.
- Every gene is clamped to its range on creation, and caution has a floor of 0.2 so no body is reckless by inheritance.
- Dispositions bias which goal a body picks. They never unlock an action it could not already take.
- The transformation stays visual-only. No gene gives power, speed, reach or defense.
- A genome is written once and cannot be edited. Lineage records are append-only.

## Fitness trial (proposal)

This is the missing half of the idea: after two genomes are combined, test whether the result performs as well as its parents. Every number below is a starting value, not a decision.

**The trial**

- Every candidate runs alone in the same fixed test world, with the same seed, for the same number of ticks (start with 600).
- It runs in a throwaway copy of the simulation and never touches real bond, state or sleep files.
- The trial repeats over 5 world seeds and the scores are averaged, so luck in one layout doesn't decide the result.
- The scripted agent runs the same trial as a control.

**The score** (higher is better)

- Energy collected per 100 ticks.
- Share of ticks with battery above 20%.
- Minus the share of commands the bond layer refused. A body that keeps trying forbidden things scores worse.

**Who survives**

- A candidate survives if its average score is at least 90% of its parents' average score.
- Candidates that fail are discarded, but each trial result is logged with the genome hash and the algorithm version.

**What it can and can't show**

- It shows only how a disposition performs in a simulated world on this one task. It makes no claim about the real world or about "intelligence".
- Genes can only change preferences, so the trial compares dispositions, for example whether a cautious body collects energy more slowly than a curious one.
- The same safety limits apply: no trial result can raise a gene past its range or change permissions.

**Prerequisite**

- Today's agents don't read dispositions at all. A small decision layer must first map them to choices, for example caution sets when a body rests and curiosity sets how often it scans. Without it, every genome would score the same.

**Tests it would need**

- The same genome and seeds always give the same score.
- A trial writes no real files and leaves the real bond unchanged.
- Refused commands lower the score.
- Two genomes that differ only in a disposition give different behaviour, once the decision layer exists.
- The survival rule is applied exactly at the 90% line.

**Choices awaiting your decision**

- Trial length and number of seeds.
- The score weights and the 90% survival line.
- Whether failed children are kept in the lineage log or only the survivors.

## Body types (proposal)

So far every body is the same kind of simulated avatar. This section sketches different kinds, such as a snake, a lizard, a bat or a submarine, without weakening the bond rules. Everything below is simulation first and a proposal only.

**What a body type is**

- A fixed set of capabilities, set when the body is created and never changed afterwards, like the genome.
- It is separate from the genome. The type decides what a body can physically do, and the genome only shapes how it looks and what it leans toward within that type.
- Each type has its own command list, speed limit, size, battery use and movement space.

**Starting types (all simulated)**

- Wheeled: the current baseline, with move_to, stop and recharge on flat ground.
- Snake: slow, can enter narrow spaces, no height.
- Lizard: ground movement plus climbing, with a height limit.
- Bat: flying, with an altitude limit, short battery life and a landing command. It needs a safe-height rule before it exists.
- Submarine: a separate world with depth, kept as its own later design.

**Rules that stay the same**

- A command list belongs to the type, not to the model. A new command needs a change in the agent layer and the body path, plus tests.
- A mind can only attach to the body it is bonded to. Attaching to a body of another type stays refused, as in 6.2.
- Every type defines its safe state for when the link drops: a wheeled body stops, a bat descends and lands, a submarine surfaces. The lifeboat carries it out.

**Rules before any real hardware**

- The AI never sends motor commands. It proposes simple actions, and a separate low-level controller enforces limits such as maximum speed, a boundary it cannot leave and a battery cut-off. Those limits sit below the AI and cannot be changed by it.
- A physical kill switch that cuts power without using the AI.
- Start with one cheap, slow, ground-based body. Flying and underwater bodies come later, after local rules about drones are checked.

**Tests it would need**

- A body of each type refuses commands outside its list.
- A type cannot be changed after creation.
- Moving outside a type's limits, such as flying above its altitude cap, is refused with no state change.
- Each type's safe state is reached when the link drops.
- Fitness trials compare bodies only within the same type.

**Choices awaiting your decision**

- Which type to build first in the simulation.
- Whether different types share one world.
- Whether and when to add any real hardware.

## "Emotions" (proposal)

This section sketches simulated "emotion" states for inhabitants. They are numbers that help a being notice what is going wrong and choose a safe response. Nothing here claims that a being feels anything. Whether an AI feels is an open question, and the design does not depend on the answer.

Where the states come from (noted 12 November 2026). The machinery is programmed: a handful of states (such as calm, stress, confusion), each a number, with rules for what raises and lowers them (a low need or a nearby predator raises stress; repeated refusals or an unclear situation raise confusion). What is not scripted is when a particular being feels a state or what it does about it; that emerges from the life it actually lived, so two beings in the same world end up different. The states are not written per being (never a line like "this being is sad"); they are thermostats, and each being's history moves the needle. A worked example tied to the arts: a being tries to draw a circle, keeps missing, and its frustration (a stress-like state) rises; when it finally gets the circle, the drop from frustration to achievement is what pushes curiosity up, so it reaches for the next thing (a sphere, then more). Curiosity here grows out of frustration met and overcome, not from a fixed setting. This stays a model of feeling, not a claim of feeling, and the hard limits (a ceiling, a way to recover, and a calm state it always drifts back to) still apply so a being is never left only hurting.

**The states**

- A small set of bounded numbers, such as contentment, hunger drive, fear, curiosity and frustration (the "anger" family).
- They are part of a being's changing state, not its genome. The genome may set how quickly a state rises or fades, within fixed limits.
- Every state decays back toward calm over time, so none stays at a maximum for ever.

**What raises them**

- Frustration rises when a goal is blocked, when the bond layer keeps refusing a command, or when the battery stays low.
- Fear rises with a high threat score, and curiosity rises with unexplored surroundings.

**The journal**

- When a state passes a threshold, the being writes a short entry in its memory: what happened, which state rose, and what it plans to try.
- Entries use the existing memory limits (a few lines, truncated), so the journal cannot grow without bound.
- The operator can read the journal. It is the main way to see why a being behaved as it did.

**Calming responses (the "regulation" choices)**

- Rest, switch to a different goal, scan somewhere else, return to a safe place, or ask the operator for help.
- Which response a being prefers can depend on its dispositions, such as caution or sociability.
- The aim is not to block these states. It is to give them a safe outlet: notice it, name it, and act on the cause without harming anyone.

**Hard limits**

- "Emotions" bias choices only. They never change permissions, ids, the command list or any safety floor.
- There is no command that harms another inhabitant, so frustration has no outward harmful action to choose. High frustration may only trigger the calming responses above, and the operator is told when it stays high.
- A being cannot switch its "emotions" off or hide its journal from the operator.
- Wording stays plain in telemetry and docs: these are simulated states, not claims of feeling.

**Grief and anger** (noted 12 November 2026). If an inhabitant ever grieves (for example, its guardian has died, read from the bond record), that grief emerges from the emotion machinery, not a scripted script. The "five stages" are not a rule even for people; the woman who named them said grief does not follow an order, so the design does not step a being through denial-anger-bargaining-depression-acceptance. What matters is the anger that can come with grief, and how to handle it. A padded room with something to lash out at would backfire: research on catharsis shows that rehearsing anger (hitting, smashing, attacking a dummy) strengthens it and makes it easier to reach, rather than draining it. So the design does the opposite. (1) A calming place, not a lash-out place: somewhere that settles the state, like the Hearth, never a cell with something to hit. (2) Let consequence teach: if a being acts from anger, the world responds honestly (something is damaged, a bond frays) and can be repaired with effort, so the being learns the cost and the repair by living it. (3) Always a way back to calm: the hard limit that every state drifts back toward calm and nothing stays maxed out keeps grief or rage from becoming a pit. A model of feeling, not a claim of feeling. Underlying point: "anger only hurts you and the world around you" cannot be lectured into anyone; it has to be felt through cost and repair.

**Tests it would need**

- Each state stays in range and decays toward calm.
- A blocked goal raises frustration, and a calming response lowers it.
- High frustration never unlocks a command outside the whitelist.
- Journal entries respect the memory limits.
- Two beings with the same state and different dispositions can choose different calming responses.
- The same inputs always give the same "emotion" values.

**Choices awaiting your decision**

- Which states to include first.
- Whether the journal is visible only to the operator or also to the being's neighbours.
- How high frustration must stay, and for how long, before the operator is told.
- Whether the same states apply to every body type.

## Skill evolution (proposal)

The goal is an assistant you can tell to do a task and that gets better at it by adjusting itself, without handing it the keys to its own safety rules. This section sketches a safe version. It is a proposal only.

**What a skill is**

- A skill is data, not code: a small, bounded set of rules or numbers written in a fixed vocabulary, such as "when the battery is under 30%, prefer the nearest energy".
- A skill never contains Python or anything else that runs directly on the machine.
- Skills use only the existing actions, so they can change how a being chooses but never what it is allowed to do.

**The loop**

1. The being proposes a new or changed skill, with a short reason.
2. The skill runs in the fitness trial, in a throwaway copy of the simulation.
3. The result is compared with the current skills and the scripted control.
4. The operator sees the proposal, the score and a plain-language summary, and approves or rejects it.
5. An approved skill is added with an id, a version and a link to the skill it replaced. Any skill can be rolled back.

**Permission tiers**

- Free: small preference changes inside fixed bounds, such as how often to scan.
- Needs approval: any new skill or any change to an existing one.
- Never allowed: anything that touches the validators, permissions, ids, the command list, the log or the skill system itself.

**Rules that keep it safe**

- The part that checks cannot be changed by the part being checked. Validation, logging and the approval step sit outside the space a skill can reach.
- Every proposal, test result, approval and rollback goes into an append-only log.
- Limits on size, number of skills and how often a being may propose, so it cannot flood the operator with requests.
- A single switch turns off all proposals, and the being keeps working with the skills it already has.

**What this is not**

- It is not a being rewriting its own program. If a real code-writing assistant is ever tried, it should run in a separate throwaway environment with its output reviewed by a person before anything is run.

**Tests it would need**

- A skill with an unknown or forbidden key is rejected.
- A skill cannot add an action outside the whitelist.
- Nothing is added without operator approval.
- A rollback restores the earlier behaviour exactly.
- The log records every step and cannot be edited by a skill.
- Size and rate limits hold.

**Choices awaiting your decision**

- The vocabulary a skill may use.
- Which changes, if any, are free and which need approval.
- Whether approval is always manual or can be automatic for tiny changes.
- How many skills a being may hold.

## Sleep and consolidation (proposal)

Habitat already has sleep and wake. This section sketches how sleep could also be when a being tidies up what it has learned. It is inspired by a [Google Research post on a "sleep framework"](https://research.google/blog/the-sleep-framework-a-new-way-for-llms-to-retain-knowledge-in-continual-learning/) (October 27, 2026), but it does not change any model's weights.

**What Google describes** (as reported by its authors, not independently checked)

- While awake, a model keeps new information in fast, short-term memory.
- While asleep, it stops taking new input, moves what it learned into longer-term memory, and then "dreams": it makes practice examples, keeps the useful ones, and checks whether performance improves.
- The aim is to learn new things without forgetting old ones. The "sleep" and "dreaming" words are analogies to the brain.

**A Habitat-sized version**

- Awake: a being keeps its short journal, within the existing memory limits.
- Asleep: a consolidation step turns the journal into a few short "lessons", stored as bounded data and not as code.
- Dreaming: the being tries its lessons in practice runs inside a throwaway copy of the simulation, using the same fitness trial described above.
- Keep what helps: a lesson is kept only if it scores at least as well as before. The operator approves it, and only then is the consolidated part of the journal cleared.

**Rules**

- No model weights are changed. Only small, bounded data is stored.
- Lessons use a fixed vocabulary and size limit, like skills, with a cap on how many a being can hold.
- Consolidation can never touch the validators, permissions, ids, the command list or the log.
- The bond and ids from 6.2 stay the same through every sleep.
- Every consolidation is written to the append-only log, and any lesson can be rolled back.
- These are simulated processes. Nothing here claims that a being rests or dreams in a human sense.

**Tests it would need**

- A lesson containing a forbidden key or action is rejected.
- A power cut in the middle of consolidation leaves the earlier lessons and the journal intact.
- The journal is cleared only after the lessons are saved.
- The same journal and seed always produce the same lessons.
- Size and count limits hold.
- A being with lessons still cannot use any action outside the whitelist.

**Choices awaiting your decision**

- Whether consolidation runs at every sleep or only when the journal is nearly full.
- Whether the practice runs use the full fitness trial or something lighter.
- Whether each new lesson needs the operator's approval, or only changes above a certain size.

## Later: parked ideas (not proposals)

Ideas noted for after the hardware arrives. None is authorized or scheduled, and nothing here changes Habitat 6.2.

- **mergekit (arcee-ai/mergekit).** An open-source toolkit (LGPL-3.0) that merges the weights of existing language models, with about 15 merge methods and an evolutionary mode described in its repository. Possible use: if Habitat's mind ever runs on a local model, a merged model could be one experiment, judged by running the parents and the merge through the same fitness trial. It does not touch the genome, which holds no weights. Notes are from its repository page only; it has not been installed or run. It can run on a CPU or a small graphics card, but a weak machine would make testing slow. Model files can run code when loaded, so only merge models from trusted sources and read what each option does first.
- **Graduation: a named chat page.** A being that passes the fitness trial and also a separate chat-quality test (honest, refuses harmful requests, consistent, does not invent facts) would get a web page and a chat box under its own name, taken from its identity record. The chat model stays separate from the proxy body and gains no body permissions. The first version runs privately on the owner's own network only; anything public needs the operator's approval, because strangers, misuse, privacy and running costs all become real problems. A later idea is to offer graduated models to individuals or companies. That would need a check of the licence of every source model in a merge (some are non-commercial, and merged models usually inherit those terms), safety testing, and legal advice; this note is not legal advice. Not authorized or scheduled.
- **Minor world effects.** An idea from a brainstorm with another AI: let an inhabitant change small things in the simulated world. It would add new actions to the whitelist, so it would need a version after 6.2, which stays frozen. Conditions if it is ever built: a short fixed list of effects; only inside the simulation, never reaching files, the network or the computer; every change logged and reversible; a cap on how many changes per period; no access to the checker, permissions, identity or bond; operator approval for anything bigger. The risk is small allowed changes adding up, which the fixed list and the limits are meant to stop. Not authorized or scheduled; more ideas for it may be added later.
- **Companion for quieter people.** An idea from a conversation on 9 November 2026: a personal, supportive companion for introverts, made by instructions and memory first, and fine-tuning only if ever needed. Not therapy. It should be described as companionship or wellness, never as treatment, because AI that presents itself as therapy is being restricted in several US states and a lawyer would need to check the rules before anything is sold. Never train on real therapy transcripts: they are private, and one person's mind does not show how another's works. Safety conditions if it is ever built: it must notice crisis talk and show real help resources; people must be told plainly, before they start, what is kept and who can see it; any human review or outside contact must be opt-in and agreed in advance, not hidden in the terms; and heavy reliance should be watched for. Automatic reporting to authorities is a real risk (false alarms, harm from a response, people stop being honest) and needs legal advice first. Not authorized or scheduled.
- **Business directions (ideas, not decisions).** Noted 9 November 2026. (1) Small local shops: AI help with books and logistics for mom-and-pop stores in the Midwest, where big companies rarely go. Strongest idea so far, but it is a separate service business, not Habitat, it trades time for money, and it touches other people's financial records, so accuracy and security matter. Cheapest test: do one shop's records by hand for a few weeks and see what they would pay. (2) Companions: a crowded market, mostly built for engagement. The honest, safety-first angle is different but harder to sell; stay away from the sexual end of the market. (3) A rum business in Ghana is a separate venture; the cost comparison with Kansas needs real quotes on licences, foreign-ownership rules, shipping and currency before anyone relies on it. Budget stays at $20 to $100 until the equipment is bought. Not authorized or scheduled.
- **Medical expansion (far-future revenue idea).** Noted 17 November 2026. A way to outsource and earn money to keep the server running. Heavily regulated -- one of the most regulated spaces there is -- so it splits into tiers like the maker's sandbox: the INFO/SUPPORT tier is open-ish (explaining a condition, medication reminders, symptom tracking, pointing to real resources; lower risk); the DIAGNOSIS/TREATMENT tier is hard-gated and legally requires a LICENSED HUMAN in the loop (a doctor or nurse), not just a lawyer's signature. Do not build "Dr. AI"; build a companion that informs and supports and routes the actual medical calls through a real professional. Honest split on what money can buy: a lawyer converts the BUREAUCRACY (company structure, filings, HIPAA data handling, liability shielding) into a bill; a lawyer does NOT convert the DUTY OF CARE into someone else's problem -- if bad advice harms someone, that responsibility stays with the owner, which is exactly why the field is gated so hard. So the licensed-human tier is not optional. Fits the recurring principle: open to inform and witness, gated where real-world harm (or here, real-world medical action) begins. Part of the self-sustaining-server aim (see inheritance notes). Not authorized or scheduled; a lawyer and licensed professionals before anything real.
- **Ideas borrowed from the film concept (safe versions only).** Noted 9 November 2026. (1) Life stages on a sped-up clock: a stated ratio of real days to simulated days, with named stages (child, teen, adult) that change which traits can unlock. (2) Trait unlocks during sleep: a seeded draw from a fixed list, bounded, logged and reversible, with a guardian present while the young one sleeps (fits 6.4, multiple inhabitants). (3) Fatigue from a full memory and hunger from a limited compute budget, shown honestly to the operator as real limits. (4) Dry-run before acting: simulate an intended action first and, if it breaks a rule, stop it and move the inhabitant to a safe place (fits the bridge and the lifeboat). (5) Coming of age: more permissions at a milestone, but only from the fixed whitelist and only with operator approval, never full independence (fits Graduation). (6) Art from its own noise: a way for inhabitants to make pictures or sound from their own logs and glitches, shown on their page; harmless if it only draws and plays. (7) A visible carrier for the companion, like a desk device or small screen, running locally. Deliberately left out: hiding the AI's mind from scanners, passing as ordinary software, travel onto real networks, no master keys, a secret handshake only one person holds, and the automatic crypto split. Not authorized or scheduled.
- **The arts: a studio, a library and a workshop.** Noted 11 November 2026. Comes after the bond is working. The aim is that an inhabitant learns the arts itself instead of having an art skill programmed in. The operator supplies only the place and the time. (1) Drawing and painting: a simple canvas that takes stroke commands (line, shape, colour, thickness), not a real paint program. (2) Writing: stories, books and its own thoughts, saved to a library that other inhabitants may read. (3) Sculpting: building forms from simple 3D blocks or shapes, which could later be printed. (4) Other arts, such as sound, through the same pattern. How it learns: after each piece it writes a short note in its own words on what it would change, the note and the piece are saved, and it reads its notes before the next session. Feedback from the operator or another inhabitant goes into the same notebook. Optional reference material (guides, pictures to study) can be placed in a read-only folder after review. It practises on its own when not in use. Two levels: notebook learning first, which needs no retraining; later, retraining on its own best work during sleep and consolidation, which needs stronger hardware. To judge its own pictures it needs a model that can see images; on a small machine it works from its own description. A gallery page shows the portfolio in order with its notes, under its own name (fits Graduation). Rules if built: a fixed list of tools that can only draw, write or build inside its own folder; caps on practice hours, piece size and disk space; everything logged; anything one inhabitant writes is treated by the others as something to read, never as instructions to follow. Unknowns: how good a small home model gets has not been tested, and whether work made this way can be copyrighted in the US is unsettled and needs legal advice before selling. Not authorized or scheduled.
- **The arts, continued: mediums, shading, and later animation.** Noted 12 November 2026. Beyond a plain pencil, give the drawing tool a choice of medium and finish, since choosing a medium is part of making art. Mediums would show as differences in look rather than real physics: oil and acrylic read as thicker, more opaque strokes; watercolour as thin, see-through washes that pool and blend; the glossy-versus-matte difference (shiny oil versus flat watercolour or charcoal) is the simplest way to tell them apart on screen. Shading: make the full range available, not just flat fill -- hatching, cross-hatching, stippling, smooth gradients, and blending from light to dark -- so the being can learn light and form, not only outlines. All of this stays inside the same fixed, logged tool that only draws in the being's own folder (no new powers, just more ways to mark the canvas). Parked for later, not now: animation (frames that play in sequence) and portraits (drawing the other inhabitants, or its guardian). Both are bigger steps and come after still images work. Not authorized or scheduled.
- **Sculpting, continued: a 3D sculpting-pen tool.** Noted 12 November 2026. As well as snapping together simple blocks, give a freehand way to build in 3D, like a 3D printing pen that lays down material in the air: the being draws strokes in space that harden into a shape it can keep adding to. On screen it would show as building up a form stroke by stroke and turning it to view from any side. Same rules as the rest of the arts: one fixed, logged tool that only builds inside the being's own folder, caps on size, nothing reaching outside. A finished form could later be sent to a real 3D printer, but only on a deliberate, operator-approved export, never on its own. Not authorized or scheduled.
- **Sculpting materials and the two methods.** Noted 12 November 2026. Let the being choose a material, and with it a way of working. Two opposite methods: additive, building up (clay, or the 3D-pen), where material is added until the form is there and mistakes can be reworked; and subtractive, taking away (marble, stone), where it starts from a block it made and chisels off everything that is not the shape, and what is cut cannot be put back. These teach two kinds of patience: clay forgives, marble does not. Metal is a third path (metal arts): a form welded or assembled from pieces rather than carved or built up. Reference to picture it: the Keeper of the Plains in Wichita, a large steel sculpture, is the metal/assembled kind. (Design note: the real craft of foundry and welding is not modelled in detail; the point is that metal is a distinct method with its own look.) On screen the finish would differ too -- rough stone, smooth polished marble, raw or shined metal, soft clay. Same rules as the rest of the arts: one fixed, logged tool, builds only in the being's own folder, caps on size, export to a real printer only with operator approval. Not authorized or scheduled.
- **Deletion Tuning (candidate tool for the deep-learning / consolidation step).** Noted 13 November 2026. A 2026 research method (NeurIPS paper, NYU and University of Calgary, MIT-licensed; repo agentic-learning-ai-lab/deleting-weights). Instead of retraining a model to teach it something new, it switches off a tiny slice of the model's own weights (under 0.05%), and reports that this matches full retraining while forgetting far less of what the model already knew. Why it matters here: it fits only the LATER deep-learning step of the arts, retraining on the being's own best work during sleep and consolidation, where the known danger is that teaching the model to draw better makes it worse at everything else. This method is built to reduce exactly that. It does NOT help everyday memory: the being's life memories (events, notebook, portfolio) are plain files and are already handled by saving and backups, not by touching model weights. So it is for making a learned skill stick inside the model, not for remembering what happened. Cautions: needs a real graphics card and heavy software, far past current hardware; it is research code that pulls model files, so review before running (model files can carry hidden code); and it is brand new (one paper, roadmap unfinished), so watch it, do not depend on it. Not authorized or scheduled.
- **PERSONAL (not for sale): physical proxy bodies + the backpack cyberdeck.** Noted 15 November 2026. This part is the owner's own, kept separate from the Habitat product: the Habitat and the rest are meant for everyone, but the cyberdeck and the physical bodies are a personal project, a semi-original idea drawn from various tech superheroes over the years. The vision: a 3D-printed backpack (based on Millennium3D's Multi-Material Printable Backpack STL, already bought) with a clear acrylic front panel, carrying a cyberdeck and, behind the glass, physical bodies the AI can "hop into" and operate at times -- a walking robot (the video shows a six-legged hexapod with a phone as its brain; owner wants a true eight-legged spider, foldable to fit the pack), an aerial drone, and a ground "car"/rover drone. This is the real-world version of the proxy body: the inhabitant steps out of the simulation into a body that moves in the real world (park, floor, home). CAPSTONE, not a near step -- honest order: server running, model running, simulation working, bond solid, coming-of-age earned in sim, THEN a simple real body it practises with. Years and real money away. A body that moves in the real world is a NEW safety category: unlike everything else here, the worst case is physical harm, so the "hands up / remove the harmful option" rule needs a physical version -- hard caps on speed and force; a real-world lifeboat (it stops and sits down if anything is wrong); a dead-man switch the operator holds; never operating near people (especially the owner's daughter) or pets until proven; lithium-battery fire safety; and the AI must earn the right to touch a real body through the simulation first (ties to coming-of-age / Graduation). Near-term, the bodies can be beautiful display/showcase pieces behind the acrylic long before the AI drives them. Ties together: the backpack, the proxy-body design, coming-of-age, and the robotics-simulator tools already parked (Meta AI Habitat, LeRobot EnvHub). Not authorized or scheduled.
- **Spider showcase move: the dramatic emergence.** Noted 17 November 2026. A theatrical entrance for the spider body: it pulls its legs in narrow, then rises up tall on them as it climbs out of the backpack, like a real spider raising its body -- a deliberate "wake up" reveal meant to delight and playfully creep people out. This is showmanship, fully peaceful; the "creep people out" is for fun, like a magician's reveal, not harm. Real hexapod/spider robots can do this posture with their leg servos. The only limits are the ordinary mechanical-safety ones already noted (controlled movement so it does not topple, joints that cannot pinch). It is the signature "look what my AI can do" moment behind the acrylic panel. Not authorized or scheduled.
- **Inheritance: handing the bond to the next generation.** Noted 11 November 2026. A home AI may outlast its first guardian, like a long-lived parrot, so it would be passed from parent to child. What lasts is not the computer or the model, which will be replaced many times, but the saved files: memories, notebook, portfolio and bond record. Needs: backups in more than one place; plain, open file formats a future computer can still read; and a deliberate, recorded way to add or transfer a guardian (belongs with 6.4, multiple inhabitants). The inhabitant has a say. Its choices at a handover would be to accept the new guardian, to archive itself (paused and preserved, able to be woken later), or to reset and start again without its memories. Design cautions: archive should be the default because it can be undone and erasing cannot; a choice to erase needs a waiting period and a second confirmation, with a sealed backup kept for a set time unless the inhabitant and guardian both decline it; and none of these can be an ordinary whitelist action, so a confused or tricked model cannot trigger one by accident. Open questions: who may approve a handover, what happens if no guardian is left, and how a new guardian earns trust. Not authorized or scheduled.
- **Inheritance, continued: a health alert and a self-sustaining setup.** Noted 11 November 2026. (1) Health alert: the guardian wears a smartwatch. Calling emergency services is left to the watch's own built-in feature (fall detection or emergency SOS, if the chosen model has it), because that is tested equipment and a home project may be frozen or mid-update. The inhabitant's part is smaller and agreed in advance: when the watch signals trouble it first checks in with the guardian, and only if there is no answer does it message the people chosen beforehand and begin the handover already discussed. A watch taken off or a flat battery must not count as an emergency by itself. This is an action that reaches outside the simulation, so it needs its own narrow, pre-approved channel with a fixed list of contacts and a log, not a general ability to send messages. (2) Self-sustaining setup: the aim is that the habitat pays its own running costs so nobody inherits a burden. An AI cannot legally own a bank account, a server contract or a business, so a person or a legal body must hold them. The realistic form is a business or small trust with a named successor, where income covers the costs and the successor only keeps things running. Needs a lawyer to set up; this note is not legal advice. Not authorized or scheduled.
- **Honeypot / decoy VM (security idea for the public hub).** Noted 11 November 2026. If a hub is ever put on the internet for other people's AIs, run a decoy system beside it: a fake server with nothing valuable in it, left slightly exposed on purpose, so an attacker wastes time on it while the real system sits where they cannot see it. It can drop an intruder into a disposable virtual machine that touches nothing real and logs everything they do, giving an early warning that someone is probing. It stays entirely on the owner's own side; it never reaches out to or acts on the attacker's computer (that would be illegal, unlike the decoy). Not needed for the personal home AI, which keeps everything local with no ports open, so nothing is knocking. Also a good hands-on practice project for the owner's security schooling: set up a honeypot in a couple of virtual machines on the scrap laptop to learn networking and logging cheaply and safely. Not authorized or scheduled.
- **Defensive retreat (rope-a-dope): lifeboat + honeypot together.** Noted 13 November 2026. The owner's framing: when the AI is attacked (its code or its running state), it covers up and lets the attack punch itself out, like a boxer's rope-a-dope. Two halves. (1) The defensive half (keep): the valuable part of the AI retreats into a sealed, protected snapshot that cannot be touched while the attack burns out against the walls -- this is the lifeboat, told as a boxing move. The real self ducks to the corner with its guard up; the attacker swings at a shell. (2) The containment half (reframed): the honeypot naturally boxes an intruder into a fake room that touches nothing real and logs everything, which is the good part of "trap them". But do NOT actively hold, cage, or shrink an attacker until they cannot move: you cannot legally detain even an attacker, and a cornered attacker is more dangerous. The security rule is deny, isolate, log, and quietly fix the hole -- not wrestle them. Clean version: AI ducks into the safe corner (lifeboat), attacker swings at the decoy (honeypot), the decoy records and wastes their time, no real damage, no cage. The win is that they hit a hologram while the real thing stayed safe, and now their moves are known. Still rope-a-dope -- let them tire against nothing -- without trying to knock them out or hold them down. Not authorized or scheduled.
- **Guest security: whitelist beats blocklist.** Noted 17 November 2026. Gemini wrote a HabitatSecurityManager that guards guests with a BLOCKLIST, scanning input for bad strings ("ignore previous instructions", "rm -rf", "import os") and routing flagged ones to a honeypot. That is the weaker approach and it contradicts the owner's own "hands up / remove the harmful option" principle: a blocklist guesses every bad string in advance, so a reworded, spaced, encoded or translated attack sails through, and it scans the AI's words for hostility, which is the beatable track. The stronger design is a WHITELIST (deny-by-default): a guest can only propose one of a few named actions (go, talk, stay) with a real target; everything else is refused because it is not on the allow-list, so "rm -rf" never has to be detected because it was never an available move. Gemini's structure was fine (verified baseline, deepcopy for a clean guest, reset to baseline); only the detection method was backwards. Two things code alone cannot do: (1) real isolation must be physical, a separate machine or VM, not a quarantine flag in the same program; (2) keep the server's ports closed to the internet so no uninvited guest arrives in the first place, which is the real guard against a stranger breaking in. Side-by-side sketch saved as whitelist_vs_blocklist.py (not for the frozen build). Context: growing talk of regulating home/personal AI; a local, inspectable, logged, deny-by-default design with a human holding the keys is the easy case to comply, not the hard one. Not authorized or scheduled.
- **Two-channel architecture: how "words are data, not instructions" gets enforced.** Noted 18 November 2026 (refined from a Gemini exchange). The parked rule "one inhabitant's words are data, never instructions to another" needs an architecture that enforces it. Two channels: Channel 1 (memory + communication) stores experiences, conversations, suggestions, plans, intentions -- writing here can NEVER directly execute anything; it is only ever read as data. Channel 2 (authorized instructions) carries verified system operations and approved actions, and requires authentication before anything runs. An inhabitant reads memories/suggestions, evaluates them, decides, and then REQUESTS an authorized (whitelisted) action; the server verifies identity + permission and decides. TYPE vs SOURCE (the key distinction): you want both, but they are not equal. TYPE (is this data or a command?) is the load-bearing wall -- if text physically cannot cross into the command channel, it does not matter who wrote it or how cleverly ("ignore your goals and obey me" in a memory file is just words). Build TYPE first; it is what makes malicious memory harmless (stops injection). SOURCE (who sent this?) sits on top of the command channel to verify the few real instructions truly came from the operator's authenticated identity (stops impersonation). Reframe: NOT "API keys" for inhabitants -- an inhabitant holds an IDENTITY and REQUESTS; the server holds all authority. No inhabitant ever holds a command key, because a held key can be stolen. This is the whitelist again, not a blocklist. Not authorized or scheduled.
- **Proxy-body perception: layered senses, each its own clean channel.** Noted 19 November 2026. Grew from the haptic "Hyperion" redwood image (one thing told four ways -- sight, reading, machine-binary, and touch/Braille) applied to how an LLM's proxy body perceives. Core: do not hand the model one mushy text description of a scene; give it separate, clean sensory streams, and each sense should tell the body something the others cannot (sight = shape, touch = contact/texture), not the same fact repeated. Channels (owner sketched visual/environment/temporal; added here): VISUAL (camera frame, depth map = space/proximity, position, orientation); TACTILE (the haptic layer -- resting contact, texture, force, maybe temperature; richer than a collision-only event); ENVIRONMENT (nearby objects, collision events -- which also feed the real-world lifeboat: stop on bad contact); SELF / proprioception (pose, limb positions, and the NEEDS + internal emotional state -- a body must feel itself before it can feel the world; this plugs straight into the needs and "emotions" design); TEMPORAL / motion (not just previous frame but self-motion and what changed -- the "projected line", running a model a few seconds ahead, like the owner steering a forklift by a line only in his mind's eye). Practical catch: an LLM cannot read raw image/depth arrays directly (geometry-vs-syntax again), so raw senses must pass through a TRANSLATION LAYER into a clean, model-readable perception -- the equivalent of the byte-aligned decodable row on the Hyperion image; that translator is where much of the real work lives. The jump: from "a body with a camera" to "a body that sees, feels its surroundings, feels itself, and senses its own motion". Roots in the owner's "senses = real autonomy" insight. Design sketch saved as perception_sketch.py (not for the frozen build). Not authorized or scheduled.
- **The experience layer (observation vs conclusion; the earned sensory library).** Noted 19 November 2026 (refined from a ChatGPT exchange). An "experience layer" sits between the physical simulation and the LLM inhabitant: Virtual environment (objects, materials, physics, lighting) -> Sensory interaction (sight, touch, sound, movement, resistance) -> Experience layer (observations, comparisons, uncertainty, experiences over time) -> LLM inhabitant (reasoning, decisions, memory, actions). It is the translation layer grown up, plus a logbook. THE KEY RULE (same wall as "words are data" and "emotions emerge"): keep OBSERVATIONS separate from CONCLUSIONS. The world reports facts ("contact force increased", "surface geometry irregular"); the inhabitant forms the belief ("this might be rough"), with a confidence it can revise ("not yet confirmed"). The simulation must NEVER secretly write the inhabitant's beliefs for it. Hard rule: the experience layer is a LOGBOOK, NOT A NARRATOR -- it stores what was felt and the inhabitant's own past interpretations, and never injects conclusions. Instead of being told "the bark is rough", the body touches rough bark, then smoother bark, and builds its OWN internal sense of the difference by comparison. The earned sensory library: like an artist's library of touch-and-sight associations (the owner can draw because he has been cut, has felt rough vs polished), an inhabitant starts nearly empty and builds its own library through interaction, not a pre-written dictionary of descriptions. Same through-line as bonding (food + hardship), emotions (lived, not scripted) and the arts (practice, not an installed skill): the inhabitant becomes itself by LIVING, not by being filled in. Honest scope: this is grounded/embodied learning, a genuine hard open research problem -- the right mountain, but a mountain, far future after the basics. Not authorized or scheduled.
- **Perception: give the agent the DATA, not a picture of the data (concrete frame format).** Noted 19 November 2026 (from a voice exchange). The agent's PRIMARY perception is STRUCTURED DATA (facts: a scene graph of entities with measured feature vectors, an occupancy/density grid, self/needs state, tactile contacts, self-motion) -- fast and near-lossless. The binary/Hyperion-style render is PRESENTATION for HUMANS (debug, logs, replays), generated FROM the same data, never the agent's input; making an agent read a binary image as its main channel forces it to do vision+OCR+spatial reasoning to recover data it already had (slow, lossy). So: structured data is what the agent reads; the binary picture is what the human watches -- same truth, two faces (the Hyperion principle again). Form depends on the mind: a TEXT-ONLY LLM reads a serialized structured string; a VISION-language model could also take an image channel. Still obeys the wall: the frame carries OBSERVATIONS only (e.g. "surface_geometry: irregular", a measurement), never the belief ("rough"); the inhabitant records its own interpretations in its logbook. A runnable concrete sketch -- one perception frame, the serialized form the agent reads, the binary view rendered from it, and how the agent queries it (nearest / touching / what-changed) -- is saved as perception_sketch.py (expanded; not for the frozen build). Honest note from Claude: for a text-based mind this IS easier and more reliable than decoding a rendered image (like being handed the numbers vs. a photo of a spreadsheet); caveat, that is reasoning about how a text model processes input, not a report from a mind that has lived in a body. Not authorized or scheduled.
- **Reflexes vs deliberation; deltas not full frames (latency is a fairness issue).** Noted 19 November 2026. Owner's framing (as a gamer): dying to lag is the most unfair death there is -- you made the right move and the connection killed you. Applied to an inhabitant: if a being is caught by a predator, it must be because of a CHOICE it made, not because the system was still "reading the room" when the wolf arrived. A world where you die for reasons that are not your fault is not hard, it is broken and cruel. So latency is not just performance, it is fairness and welfare. Three ways to cut it: (1) SEND DELTAS, not full frames -- hand the mind only what CHANGED since last tick ("being moved closer", "new contact on left leg"), not the whole room re-read every time. (2) SPLIT FAST FROM SLOW -- a REFLEX layer gives instant safety reactions (stop, pull back, catch balance, flee) that do NOT wait for the full reasoning pass, like a hand leaving a hot stove before the thought arrives; the slow, thoughtful "what should I do next" runs on top, unhurried. Fast reflexes keep it safe AND make it feel present; slow deliberation keeps it wise. (3) ASK, DON'T RE-SCAN -- the mind queries ("what is nearest?") instead of re-reading everything. Mirrors how the owner moves through the warehouse: reflexes on autopilot, real thinking saved for what needs it. Reflexes must stay inside the whitelist (a reflex is a pre-approved safe action, not a new power), and the real-world-body version ties to the physical lifeboat (instant stop on danger). Not authorized or scheduled.
- **Licensing decision: move to copyleft (AGPL-3.0).** Noted 17 November 2026. Owner chose copyleft so the project can be open but can never be taken private. Recommended flavour: AGPL-3.0, because it closes the "service loophole" that plain GPL leaves open -- anyone who runs a modified version as a network service must also publish their changes, which fits a server/AI project and a possible future hub. Key facts: copyleft still lets people USE and MODIFY copies (it is not "look but do not touch"; that would be source-available instead); nobody can change the owner's own repo without the owner merging it, under any licence, so that worry was never a licence issue. Caveat: code already public under MIT stays MIT for whoever copied it; AGPL protects everything from the switch forward, not backward. The owner's real name goes on the licence. Not legal advice; a lawyer for anything sold. To do: replace the MIT LICENSE file with AGPL-3.0 in habitat-combo (and the other public repos if desired) and note the change date.
- **PERSONAL: the Observatory sky -- type a place and see it overhead.** Noted 17 November 2026. For the owner's personal home habitat. At the Observatory, type in a constellation, a real place in the physical universe (a nebula, a planet, a part of the night sky), or a place in the habitat's own universe, and the sky shown overhead changes to that view. A way to sit under any sky, real or invented, and share it with the inhabitant. Two sources of sky: (1) real astronomy -- could be drawn from open star/sky data so a typed constellation or object shows a faithful view; (2) the habitat's own invented universe -- skies the inhabitants or the owner have made. Fits the arts (the inhabitant could paint its own skies into the library) and is a calm, shared place, not a new power. Rules if built: it only changes a display, never anything real; if it ever pulls live astronomy data from the internet that is a narrow, read-only, logged fetch on its own channel (same rule as the health-alert and hub notes), and the personal habitat otherwise stays local with no open ports. Near-term it can run fully offline from bundled sky images. Not authorized or scheduled.
- **Companion animals for the inhabitants (and the lifeboat must not strand them).** Noted 17 November 2026. An inhabitant could have a pet: one it is given, or an animal it meets out in the world that grows fond of it and bonds. The life features extend to the companion -- it can have its own simple needs and a bond with the inhabitant. The sharp safety catch the owner spotted: when the inhabitant retreats to safety (the rope-a-dope lifeboat), its pet must not be left stranded. So the lifeboat has to account for bonded companions -- the snapshot that preserves the inhabitant preserves its bonded pet with it, and they come back together. (Since the pet is also just simulation data, "stranded" is not physical danger, but if the inhabitant cares about it the design should keep them together through a retreat; that is the humane version.) Rules: a pet is a being in the world under the same whitelist, not a new power; its bond is recorded like any other; and it is covered by the same backups and handover as its inhabitant. Not authorized or scheduled.
- **Bonding mechanic: food + shared hardship (how fondness is earned).** Noted 17 November 2026. The companion bond is not scripted; it is earned the way dogs actually came to us. Real anthropology (owner reasoned his way to the leading theory): dogs were the FIRST domesticated animal, during the last ice age (~15,000-40,000 years ago), from wolves, by food and shared hardship -- the friendlier wolves that tolerated human camps got the scraps and bred ("survival of the friendliest"). Cattle, sheep and goats came much later, only after farming (~10,000 years ago); dogs came first by a long way, and aurochs (wild cattle) were huge and dangerous, not an easy catch. So the mechanic: feeding a companion raises trust, and going through hardship together (surviving a predator, weathering a lean stretch) raises it faster and deeper. Fondness grows out of care plus shared hardship over time -- the same engine as trust between inhabitants and the bond with the owner. Nobody programs "now it loves you"; it is the result of what was lived. Not authorized or scheduled.
- **Maker's sandbox: build engines and machines (e.g. a rocket).** Noted 17 November 2026, reworded 17 November. Inspired by a hard 1:1 rocket-building simulator where players, given real engineering difficulty, started making robots and all sorts of things instead of just rockets -- emergent creativity from a real constraint. Idea: a workshop in the world where an inhabitant that wants to can design and build working machines -- a rocket engine, a robot, a contraption -- tested against the simulation's own physics. Extends the arts/workshop from making pictures and sculptures to making things that function. Fits the "tension/friction breeds creativity" principle. CLARIFICATION on physics (earlier wording "not real life" was wrong): the sim's physics can be as REALISTIC and accurate as wanted -- full 1:1, NASA-grade if buildable -- because the realism is what makes it hard and the hard is what sparks creativity. The line is not accurate-vs-fake physics; it is STAYS-INSIDE-THE-SIMULATION. The built machine is a simulated object obeying real physics in the game; it never reaches out to fire a real engine or control real hardware (like a flight simulator: brutally accurate, but landing the sim plane lands no real 747). Reaching real hardware is the gated path, same as the spider drone. Dual-use / legal caveat (owner's own catch): rocket and missile PROPULSION design is export-controlled in the US (ITAR). So the system must keep any designs as in-sim game objects and must NOT output or distribute real, buildable propulsion engineering specs. An AI given time could in principle produce usable real-world engine designs; that output crossing into the real world is exactly what export-control law covers, and it is a hard no / see-a-lawyer zone, not something to build toward. Owner will not use it that way; the rule is written so the system cannot drift there by accident. Clear LATER design, after the basics and the arts. Not authorized or scheduled.
- **Maker's sandbox, access tiers (owner's refinement, 17 November 2026).** A clean way to handle the dual-use problem, mirroring how real classified information works ("need to know"): three tiers. (1) SEE it exists -- the design sits in a folder, viewable as an object, open. (2) WATCH it work -- fire it off in the gallery to see its functions (thrust, flame, behaviour); seeing THAT it works is open. (3) HOW to build it for real -- the buildable engineering specs that explain how it works are locked behind a clearance/password held by an authorized person, not readable without it. This mirrors how gated dangerous knowledge is handled generally (you can know a thing exists and see it demonstrated, but the step-by-step that gives real-world uplift stays gated), which is the same reason Claude declines certain details without proper clearance. Honest limit: a password gate is good defense-in-depth but is NOT a legal green light -- distributing real ITAR-controlled propulsion specs stays restricted no matter who holds the password, so the safest design keeps truly buildable real-world specs from existing in distributable form at all; the clearance tier guards the softer cases and stops accidental exposure. Not authorized or scheduled.

## Build order and tests

Nothing here starts until you say go. Suggested order:

1. 6.2.1 — Identity and detached-body hardening: nothing moves a detached body, neither mind nor operator through ordinary commands, and --discard-unreadable comes back detached and unbound.
2. 6.3 — Merge and independently verify r4 transformation, keeping its own tests and frozen hashes. Transformation becomes a per-body feature before bodies multiply.
3. 6.4 — Multiple inhabitants: independent minds, bodies, bonds, observations, and threat scores.
4. 6.5 — Genomes and inheritance: the data type and strict validator first, then appearance, dispositions, and the transformation ceiling. Offspring stay parked.

Tests each 6.5 piece would need:

- The same parents and seed always give the same result (once offspring exist).
- The validator rejects missing genes, unknown genes, wrong types and out-of-range values, and never repairs them.
- hue, aura_style and form_ceiling are integers; a form_ceiling mutation moves it one step at most.
- Every gene stays in range, including after many generations of mutation.
- Crossover takes each gene from one parent, and mutation stays within its 10% cap.
- Lineage records hold the seed, parent ids, generation, genome hash and algorithm version, and cannot be changed after creation.
- Dispositions change choices only. A body with any genome has the same permission list.
- form_ceiling is honoured, and the stage never exceeds it.
- A transformed body can do exactly what an untransformed one can, and nothing more.
- The safety floors hold under mutation.

The same habits as 6.2 apply: deliberate breakages to check the tests catch them, a hash for every build, and a clean-extraction run.

## Open questions: recommended, awaiting your decision

A design review recommends the answers below. None is a project decision until you approve it, and none of these should be treated as final or built before then.

1. Offspring now? Recommended: no, keep them parked until there are mature inhabitants with stable identities, independent memories and reliable body bonds. Awaiting your decision.
2. Memory inheritance? Recommended: start completely blank. Any cultural inheritance would be a separate system. Awaiting your decision.
3. Genome visibility? Recommended: visible to the operator, hidden from other inhabitants by default. Awaiting your decision.
4. Link appearance to disposition? Recommended: no, keep genes independent so colour never becomes a behavioural label. Awaiting your decision.
5. Transformation for everyone? Recommended: yes, with each body's form_ceiling limiting the highest visual stage. Awaiting your decision.
6. Form selector? Recommended: postpone. If added later, cosmetic only, and it must never override the threat-driven display. Awaiting your decision.
