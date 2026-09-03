# M11 — everyday imports, and a city that is flavour rather than a job

One change, from the second smoke test and the user decision of 2026-09-02
(spec #13a as it now reads). It is a content change in the sense that most of
the diff is writing, and a design change in the sense that it is the first
milestone to move a line the game had already been built against twice.

| # | Requirement | Where it lives |
| --- | --- | --- |
| #13a | a need is an everyday, relatable thing; the city is light flavour | `content/import_needs.json`, `engine/trade.py` |
| #13, #33 | the mayor-facing slate offers everyday orders, and the seed bank is one | `engine/game.py`'s `import_choice_offer`, `content/import_needs.json` |
| #15 | an offer is still free-form and still binds nothing | unchanged, deliberately |
| #26, #30 | the paper speaks the same language as the game | `content/newspaper.json`, `newspaper/sample.py` |
| #32 | the endgame stops describing solved problems | `content/newspaper.json`'s endgame frames |

---

## 1. What the second smoke test actually found

Schema 2 was not broken. It was the fix for schema 1: the 2026-08-31 decision
had retired needs that asked exporters what a city *should do* about a civic
problem, and every seed in schema 2 named goods instead. Every deterministic
check passed. The pool was honest trade.

It was also this:

> roof trusses, ties, and a stamped calculation from somebody insured;
> a survey crew for the harbour floor; hydrophones; a seaweed baler

Which is trade, and is unplayable. The check the tests were running was *is
this goods*, and the question at the table is *can I play this*. A mayor who
draws the trusses notice has to either know something about roofs or write a
joke about not knowing something about roofs, and the second one gets old in
about two rounds. The premise underneath it — that a player is a municipal
officer with a municipal problem — was never written down as a requirement, so
it survived a rewrite that was aimed at something else.

Schema 3 retires the *subjects*, not just the framing. That is the whole
milestone, and it is why the fix could not be a patch: there is no candy seed
that used to be a bridge.

## 2. The pool (spec #13a, #33)

48 seeds across 16 categories, three per category:

| | | | |
| --- | --- | --- | --- |
| `candy` | `soft_drinks` | `snacks` | `baked_goods` |
| `hot_drinks` | `condiments` | `books` | `music` |
| `games_and_puzzles` | `toys_and_novelties` | `clothes` | `plants` |
| `pets` | `homeware` | `stationery` | `small_comforts` |

16 × 3 covers the largest possible game (10 cities × 2 rotations = 20 needs)
without any city ordering twice in one category, which is what spec #14 needs
of the bank rather than of the engine.

Three properties are doing the work, and none of them is "the words are nicer":

* **A named quantity.** Forty cases, two hundred kites, six hens, four hundred
  mugs, one cat. A number is what turns "send sweets" into something a player
  can picture loading, and it is also most of the comedy.
* **A scene that is flavour, not a problem.** A ferry waiting room, a bus depot
  canteen, one long grey street with four hundred empty window sills. It tells
  a mayor what mood to write into. It is never a thing the exporter is being
  asked to fix.
* **A wide-open middle.** "Ship us the crisps your city eats without thinking
  about it" can be answered well by anybody at the table and identically by
  nobody.

The city is still the player's persona and still the unit of scoring. What it
is no longer is a job.

## 3. Three refusals, three doors (`engine/trade.py`)

Spec #13a now names three failures, and they are genuinely different, so they
are three lists in `content/import_needs.json`'s `trade_policy` rather than one
with more entries in it:

| Refusal | Catches | Why it is its own list |
| --- | --- | --- |
| `advice_markers` | "what should we do about the sweet shop" | not an order at all — it has to be re-filed as one |
| `civic_markers` | "purchase order: pumps, hose, gravel, budget line 44-C" | a perfectly good order that asks a player to be a council officer |
| `specialist_markers` | "trusses, ties, and a stamped calculation" | honest goods that only a professional can answer well |

The distinction is not pedantry: it is what the refusal message says to the
mayor who tripped it. An advice request needs re-filing, a procurement notice
needs to stop being one a council would file, and a specialist notice needs the
everyday version of itself ordered instead. `TradePolicy.refusal_marker_in`
returns `(kind, phrase)` for callers — the conformance pass, a facilitator's
agent — that need to say which of the three it was.

All three run at all three doors a need can enter through, because a rule
enforced at two of three doors is enforced at none:

1. the **seeded list**, at load, so a drifted seed refuses to start a game;
2. a **player-suggested** addition to the pool (spec #33's extensibility);
3. an **importing mayor's freeform order** (spec #13), which is a first-class
   need and therefore not a bypass.

The affirmative half of the check is the declared `trade_family`, and its six
values were rewritten too — `sweets_and_drinks`, `snacks_and_bakes`,
`reading_and_listening`, `play_and_pastimes`, `wear_and_comfort`,
`plants_and_pets`. The retired families (`materials`, `equipment`,
`specialist_services` and the rest) are not among them, so a need still
declaring one is refused at the door and a fixture written against schema 2
fails loudly instead of quietly reintroducing the premise.

## 4. What the mayor actually reads

The milestone's acceptance condition is about the *offer*, not the pool: a seed
rewrite that left the mayor-facing prompts talking about survey crews would
have changed the data and not the game. So `import_choice_offer` carries
`TradePolicy.describe()` — the six families with concrete examples ("boiled
sweets by the jar", "soft drinks in glass bottles, by the crate", "two hundred
second-hand paperbacks"), the note to the mayor, and the three refusals in
words rather than as a regex. `tests/test_import_choice.py` pins candy, soft
drinks and books in what a real slate hands a real mayor, and separately checks
that every suggestion on every slate in a live game is free of all three
markers.

## 5. The paper had to stop talking like a council too

`content/newspaper.json` is keyed by category in three places — the editorial
asides, the arrival lines the consequences column uses, and the SVG palettes —
so retiring 16 categories retired 48 lines of copy and 16 colour schemes with
them. They are rewritten, not remapped: the `pets` aside is about the animals
having been here first, the `stationery` one is about a pen borrowed from the
front counter and never returned.

Two frames elsewhere were describing a game that no longer exists and are now
fixed at the source rather than at the seam:

* the endgame's imports line said each notice was "a problem it could not solve
  alone" — it is now "a thing it wanted and could not get at home";
* the zero-submission line said the city "solved its own problem" — it now
  "made its own", which is what spec #17's ramp-up has always actually been.

`newspaper/sample.py`'s twelve-round sample game was re-written around the new
pool for the same reason, since a committed sample is the thing a reader looks
at first.

## 6. The recorded game was re-recorded, not patched

`playtest/transcript.json` is eight mayors over seventeen rounds, each played
by its own separately-spawned agent session given only its own city's brief
(spec #34). Every notice in it came from the retired pool, so every offer in it
was an answer to a question this game no longer asks. Patching the notices and
keeping the offers would have produced a transcript in which nobody was
answering what they were asked — a fixture that passes while lying about its
own provenance.

So the briefs were regenerated from the new pool and the game was played again,
seat by seat. The result: 17 editions, `playtest/conformance.json` at **30
passing, 4 handed to the Evaluator with the material to judge, 3 not decidable
from game state**, and `#13a` now reporting all six everyday families across
ten of the sixteen categories.

## 7. What re-recording found: verbatim text meets the tone gate

The new recording would not publish. Edition 14 raised, and the cause was one
clause in a winning offer:

> ... enough nonsense for four hundred years and roughly one year per stupid
> remark.

`stupid` is in `content/newspaper.json`'s forbidden register (spec #30), the
paper reprints a **winning** offer verbatim, and a register hit refuses the
edition rather than printing it. The gate was right — that is exactly the job
it was built for — and the failure was upstream of it: the mayors' briefs told
each agent the privacy rules that bound its writing and said nothing about the
publication rules that also bound it. A player was being held to a standard it
had not been shown.

So `playtest.briefing._publication_note` now puts that in every brief: that a
winning offer is printed exactly as written, that the paper is pointed but
never mean about a person, and the register itself, read out of the content
file rather than restated — so a term added to the paper's policy reaches the
players who have to respect it instead of quietly becoming a trap. Valparaíso's
round-12 offer was then reissued by its own session under the corrected brief,
which is the only way it could have been: spec #34 does not let the Generator
write a player's lines.

### One thing this did not fix

In a *live* game the same collision is still possible: a mayor submits a
free-form offer containing a register word (spec #15 says exports are
free-form, and nothing screens them at submission), it wins, and the edition
refuses to publish — which now means the round cannot complete. The recorded
game no longer trips it and the briefs make it unlikely, but "unlikely" is not
the same as "structurally impossible", and everywhere else in this deliverable
that distinction has been the whole point.

Fixing it properly means deciding *what a live game should do* with an offer
the paper will not print — refuse the submission at the door with a message,
publish around it, or something else — and that is a spec question rather than
a content one, since spec #15 makes the offer free-form and spec #30 makes the
edition clean. It is recorded here and reported to the Coordinator rather than
settled inside this milestone.
