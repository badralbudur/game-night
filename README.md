# Sister Cities (deliverable repo)

This is the **deliverable** for the game-night-harness project — the
actual game being built, not the harness that builds it.

The game is **Sister Cities**. Its in-fiction newspaper is **The Daily
Manifest**. See [`NAME.md`](NAME.md) for why, and [`content/`](content)
for the seeded game content (import needs, city gazetteer, mayor
questions). All configurable parameters live in
[`config.json`](config.json).

- Harness (process, spec, decisions): https://github.com/badralbudur/game-night-harness
- This repo tracks the deliverable's own build history independently, per
  spec requirement #35 (no shared git history with the harness repo).

Work lands here one commit per harness run/milestone attempt, per spec
requirement #35's git policy. The Coordinator owns that commit; the
Generator writes the files and the Evaluator grades them.

The requirements this deliverable is built against live in the harness
repo's `spec.md` — deliberately not mirrored here, so there is exactly
one authoritative copy and no chance of grading against a stale
snapshot.

## What exists so far

| Milestone | Status |
| --- | --- |
| **M1** — seeded game content ([`content/`](content), [`NAME.md`](NAME.md)) | built |
| **M2** — core round-flow engine ([`engine/`](engine), [`tests/`](tests)) | built — see [`docs/m2-engine.md`](docs/m2-engine.md) |
| **M3** — economy: profit rolls, leaderboard, exposure ([`engine/economy.py`](engine/economy.py)) | built — see [`docs/m3-economy.md`](docs/m3-economy.md) |
| **M4** — facilitator questions: two-slot check-in, framing, aggregate data ([`engine/aggregate.py`](engine/aggregate.py)) | built — see [`docs/m4-questions.md`](docs/m4-questions.md) |
| **M5** — newspaper rendering core: prose, redaction, tone, one image per edition ([`newspaper/`](newspaper), [`content/newspaper.json`](content/newspaper.json)) | built — see [`docs/m5-newspaper.md`](docs/m5-newspaper.md) |
| **M6** — publication & archive: the private address, the browsable back issues, the curated public manifest ([`hosting/`](hosting), [`site/`](site)) | built — see [`docs/m6-hosting.md`](docs/m6-hosting.md) |
| **M7** — the last edition: the crown, the twist article, a portrait per city ([`newspaper/endgame.py`](newspaper/endgame.py), [`engine/endgame.py`](engine/endgame.py)) | built — see [`docs/m7-endgame.md`](docs/m7-endgame.md) |
| **M8** — one whole game, played by eight separate agents, with all thirty-five rules checked at once ([`playtest/`](playtest), [`engine/join.py`](engine/join.py)) | built — see [`docs/m8-integration.md`](docs/m8-integration.md) |

The engine covers the round timer and its lockstep, the city order queue and its
two rotations, the import/export/winner cycle with every fallback, the import
repetition rule, blind-voting data handling, the economy — profit rolls, the
cumulative per-city leaderboard, and the exposure policy around both — and the
mayor questions: the two-slot check-in, the framing rules, and what a round's
answers add up to.

The newspaper turns that into **The Daily Manifest**: one edition per completed
round, written from the frames in [`content/newspaper.json`](content/newspaper.json),
with mayors named by city and office only, the aggregate item written in wording
the arithmetic actually licenses, and one image per edition. Run the tests with:

```
python3 run_tests.py
```

A rendered twelve-round sample game is committed at
[`editions/sample-game/`](editions/sample-game) —
[`index.md`](editions/sample-game/index.md) is its archive index. This
deployment has no image-generation provider configured, so every edition uses
the permitted deterministic SVG fallback and records that in its own
`image.provenance`.

[`hosting/`](hosting) publishes those editions as the paper itself: one fixed,
unguessable, `noindex` address with every back issue still browsable at it
(spec #26–#27). The built site is committed at [`site/`](site) —
`site/public/` is exactly what is served and
[`site/publication-manifest.json`](site/publication-manifest.json) records why
each file in it is public. The address is **not** in any of it, and is not in
this repo: it lives in a `0600`, git-ignored `.site-id`, and the build refuses
to publish anything containing it. Serve it with `python3 -m hosting.serve`,
which prints the URL.

When a game reaches its end condition the paper prints one more issue: **the
final edition** (spec #31–#32), which crowns the cumulative-profit winner, runs
a tongue-in-cheek piece on what the year's trade actually did to everybody, and
gives every city a description and a portrait drawn from its own history — with
the offers it received and declined printed as its "excess", and the offers it
*sent* and nobody chose named as existing and deliberately not itemised, because
spec #21 outlives the game. That argument is the whole of
[`docs/m7-endgame.md`](docs/m7-endgame.md), and it is worth reading before the
code. The sample run's last edition is
[`editions/sample-game/final.md`](editions/sample-game/final.md).

## One whole game

[`playtest/`](playtest) is the integration pass: **one complete game of eight
mayors over seventeen rounds**, each mayor played by its own separately spawned
agent session given only its own city's brief, then recorded so it replays move
for move forever. Run it with:

```
python3 -m playtest.run              # replay, publish, build the site, report
python3 -m playtest.run --check      # the report only; writes nothing
```

It publishes to its own private address at [`site/playtest/`](site/playtest) —
spec #27 makes an address an append-only archive, so a second game gets a second
address rather than overwriting the first — and it checks spec #1–#35 against
the finished game, its editions and its published bytes in one pass:
[`playtest/conformance.json`](playtest/conformance.json), 28 passing, 4 handed to
the Evaluator with the material to judge, 3 that are not decidable from game
state and say so. What a whole game found that the per-milestone tests could not
is written up in [`docs/m8-integration.md`](docs/m8-integration.md).

Joining is [`engine/join.py`](engine/join.py): a duplicate city pick is
reassigned to a geographically close alternative by the procedure written down in
`content/gazetteer.json`, and announced — never silently allowed to collide
(spec #2).
